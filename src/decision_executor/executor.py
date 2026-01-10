"""
Decision Executor Module

This module applies rules to scenarios and tracks execution results:
1. Batch execution of rules across scenarios
2. Storage of outcomes and rule activation paths
3. Analysis of rule coverage and conflict patterns
4. Identification of decision boundaries

Design Philosophy:
- Track everything for later analysis
- Identify patterns in rule activation
- Enable detection of conflicts and instabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter


class DecisionExecutor:
    """
    Executes rules against scenarios and analyzes execution patterns.
    
    This executor maintains a history of all decisions made, enabling
    downstream analysis of rule conflicts, coverage, and instability.
    """
    
    def __init__(self, rule_engine):
        """
        Initialize the decision executor.
        
        Args:
            rule_engine: Initialized RuleEngine instance
        """
        self.rule_engine = rule_engine
        self.execution_history = []
        self.scenario_results = []
    
    def execute_batch(self, scenarios: List[Dict], 
                     store_audit_trail: bool = True) -> pd.DataFrame:
        """
        Execute rules against a batch of scenarios.
        
        Args:
            scenarios: List of scenario dictionaries
            store_audit_trail: Whether to store detailed audit trails
            
        Returns:
            DataFrame with execution results
        """
        results = []
        
        for i, scenario in enumerate(scenarios):
            # Execute rule engine
            decision_result = self.rule_engine.execute(scenario)
            
            # Build result record
            result = {
                'scenario_id': i,
                'decision': decision_result['decision'],
                'rule_id': decision_result['rule_id'],
                'confidence': decision_result['confidence'],
                'reasoning': decision_result['reasoning']
            }
            
            # Add scenario features
            for key, value in scenario.items():
                result[f'feature_{key}'] = value
            
            # Store detailed audit trail if requested
            if store_audit_trail:
                result['audit_trail'] = decision_result['audit_trail']
                result['matched_rule'] = decision_result['matched_rule']
            
            results.append(result)
            
            # Store in history
            self.execution_history.append({
                'scenario': scenario,
                'result': decision_result
            })
        
        # Convert to DataFrame for analysis
        df_results = pd.DataFrame(results)
        self.scenario_results = df_results
        
        return df_results
    
    def get_decision_distribution(self) -> Dict[str, int]:
        """
        Get distribution of decisions across all executed scenarios.
        
        Returns:
            Dictionary mapping decision outcomes to counts
        """
        if len(self.scenario_results) == 0:
            return {}
        
        return self.scenario_results['decision'].value_counts().to_dict()
    
    def get_rule_activation_stats(self) -> pd.DataFrame:
        """
        Get statistics on how often each rule was activated.
        
        Returns:
            DataFrame with rule activation statistics
        """
        if len(self.scenario_results) == 0:
            return pd.DataFrame()
        
        rule_stats = self.scenario_results.groupby('rule_id').agg({
            'scenario_id': 'count',
            'confidence': 'mean',
            'decision': lambda x: x.mode()[0] if len(x) > 0 else None
        }).reset_index()
        
        rule_stats.columns = ['rule_id', 'activation_count', 'avg_confidence', 'primary_decision']
        rule_stats = rule_stats.sort_values('activation_count', ascending=False)
        
        return rule_stats
    
    def find_decision_boundaries(self, feature_name: str, 
                                decision_pairs: Optional[List[tuple]] = None) -> List[Dict]:
        """
        Find decision boundaries for a specific feature.
        
        Identifies points where small changes in a feature value lead to
        different decisions - potential instability zones.
        
        Args:
            feature_name: Name of feature to analyze
            decision_pairs: Optional list of (decision1, decision2) tuples to focus on
            
        Returns:
            List of boundary point dictionaries
        """
        if len(self.scenario_results) == 0:
            return []
        
        feature_col = f'feature_{feature_name}'
        if feature_col not in self.scenario_results.columns:
            return []
        
        # Sort by feature value
        sorted_df = self.scenario_results.sort_values(feature_col)
        
        boundaries = []
        for i in range(len(sorted_df) - 1):
            curr_row = sorted_df.iloc[i]
            next_row = sorted_df.iloc[i + 1]
            
            # Check if decision changes
            if curr_row['decision'] != next_row['decision']:
                # Filter by decision pairs if specified
                if decision_pairs:
                    decision_pair = (curr_row['decision'], next_row['decision'])
                    reverse_pair = (next_row['decision'], curr_row['decision'])
                    if decision_pair not in decision_pairs and reverse_pair not in decision_pairs:
                        continue
                
                # Calculate boundary characteristics
                boundary = {
                    'feature': feature_name,
                    'value_before': curr_row[feature_col],
                    'value_after': next_row[feature_col],
                    'value_gap': next_row[feature_col] - curr_row[feature_col],
                    'decision_before': curr_row['decision'],
                    'decision_after': next_row['decision'],
                    'rule_before': curr_row['rule_id'],
                    'rule_after': next_row['rule_id'],
                    'confidence_before': curr_row['confidence'],
                    'confidence_after': next_row['confidence']
                }
                
                boundaries.append(boundary)
        
        return boundaries
    
    def find_conflicting_scenarios(self, perturbation_threshold: float = 0.05) -> List[Dict]:
        """
        Find scenarios where similar inputs lead to different decisions.
        
        This identifies potential conflicts or instability in the rule set.
        
        Args:
            perturbation_threshold: Maximum relative difference between features
                                   to consider scenarios as "similar"
            
        Returns:
            List of conflict dictionaries
        """
        if len(self.execution_history) < 2:
            return []
        
        conflicts = []
        
        # Compare each scenario with others
        for i in range(len(self.execution_history)):
            for j in range(i + 1, len(self.execution_history)):
                scenario1 = self.execution_history[i]['scenario']
                scenario2 = self.execution_history[j]['scenario']
                result1 = self.execution_history[i]['result']
                result2 = self.execution_history[j]['result']
                
                # Check if scenarios are similar
                if self._are_scenarios_similar(scenario1, scenario2, perturbation_threshold):
                    # Check if decisions differ
                    if result1['decision'] != result2['decision']:
                        conflicts.append({
                            'scenario1_id': i,
                            'scenario2_id': j,
                            'scenario1': scenario1,
                            'scenario2': scenario2,
                            'decision1': result1['decision'],
                            'decision2': result2['decision'],
                            'rule1': result1['rule_id'],
                            'rule2': result2['rule_id'],
                            'similarity_score': self._calculate_similarity(scenario1, scenario2)
                        })
        
        return conflicts
    
    def _are_scenarios_similar(self, scenario1: Dict, scenario2: Dict, 
                              threshold: float) -> bool:
        """Check if two scenarios are similar within threshold."""
        total_diff = 0
        count = 0
        
        for key in scenario1.keys():
            if key in scenario2:
                val1, val2 = scenario1[key], scenario2[key]
                
                # Handle different types
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if val1 != 0:
                        relative_diff = abs(val1 - val2) / abs(val1)
                    elif val2 != 0:
                        relative_diff = abs(val1 - val2) / abs(val2)
                    else:
                        relative_diff = 0
                    
                    total_diff += relative_diff
                    count += 1
                elif val1 == val2:
                    count += 1
                else:
                    # Different categorical values
                    total_diff += 1
                    count += 1
        
        if count == 0:
            return False
        
        avg_diff = total_diff / count
        return avg_diff <= threshold
    
    def _calculate_similarity(self, scenario1: Dict, scenario2: Dict) -> float:
        """Calculate similarity score between two scenarios (0-1)."""
        total_similarity = 0
        count = 0
        
        for key in scenario1.keys():
            if key in scenario2:
                val1, val2 = scenario1[key], scenario2[key]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    max_val = max(abs(val1), abs(val2))
                    if max_val > 0:
                        similarity = 1 - abs(val1 - val2) / max_val
                    else:
                        similarity = 1.0
                    total_similarity += similarity
                    count += 1
                elif val1 == val2:
                    total_similarity += 1
                    count += 1
        
        return total_similarity / count if count > 0 else 0
    
    def get_execution_summary(self) -> Dict:
        """
        Get comprehensive summary of execution results.
        
        Returns:
            Dictionary with execution statistics
        """
        if len(self.scenario_results) == 0:
            return {
                'total_scenarios': 0,
                'decisions': {},
                'rules_activated': {}
            }
        
        return {
            'total_scenarios': len(self.scenario_results),
            'decisions': self.get_decision_distribution(),
            'rules_activated': self.scenario_results['rule_id'].nunique(),
            'avg_confidence': self.scenario_results['confidence'].mean(),
            'scenarios_with_no_match': len(self.scenario_results[self.scenario_results['rule_id'].isna()])
        }
    
    def export_results(self, filepath: str, include_audit_trail: bool = False):
        """
        Export execution results to CSV.
        
        Args:
            filepath: Path to save results
            include_audit_trail: Whether to include audit trail (may be large)
        """
        if len(self.scenario_results) == 0:
            return
        
        df_export = self.scenario_results.copy()
        
        if not include_audit_trail:
            # Remove audit trail columns
            df_export = df_export.drop(columns=['audit_trail', 'matched_rule'], errors='ignore')
        
        df_export.to_csv(filepath, index=False)
    
    def reset(self):
        """Clear execution history and results."""
        self.execution_history = []
        self.scenario_results = []
