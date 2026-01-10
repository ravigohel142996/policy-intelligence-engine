"""
Policy Repair Engine Module

This module enables What-If analysis by:
1. Simulating rule modifications
2. Comparing risk before and after changes
3. Identifying trade-offs introduced by changes
4. Suggesting optimal rule adjustments

Design Philosophy:
- Test changes in a sandbox before deployment
- Quantify impact of modifications
- Provide actionable insights for rule improvement
"""

import copy
import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ModificationType(Enum):
    """Types of rule modifications."""
    ADJUST_THRESHOLD = "adjust_threshold"
    CHANGE_PRIORITY = "change_priority"
    ADD_CONDITION = "add_condition"
    REMOVE_CONDITION = "remove_condition"
    MODIFY_DECISION = "modify_decision"
    DISABLE_RULE = "disable_rule"
    ADD_BUFFER_ZONE = "add_buffer_zone"


@dataclass
class RuleModification:
    """
    Specification for a rule modification.
    
    Attributes:
        rule_id: ID of the rule to modify
        modification_type: Type of modification
        parameters: Parameters specific to the modification type
        description: Human-readable description of the change
    """
    rule_id: str
    modification_type: ModificationType
    parameters: Dict[str, Any]
    description: str


class PolicyRepairEngine:
    """
    Engine for simulating and comparing rule modifications.
    
    Allows testing changes to rules in a sandbox environment and
    comparing their impact on risk metrics and decision patterns.
    """
    
    def __init__(self, original_rule_engine):
        """
        Initialize the policy repair engine.
        
        Args:
            original_rule_engine: Original RuleEngine instance to base modifications on
        """
        self.original_engine = original_rule_engine
        self.original_rules = copy.deepcopy(original_rule_engine.rules)
        self.modification_history = []
    
    def apply_modification(self, modification: RuleModification) -> Dict:
        """
        Apply a modification to create a new rule set.
        
        Args:
            modification: RuleModification specification
            
        Returns:
            Dictionary with modified rules
        """
        # Create deep copy of original rules
        modified_rules = copy.deepcopy(self.original_rules)
        
        # Find the target rule
        target_rule = None
        for rule in modified_rules['rules']:
            if rule['rule_id'] == modification.rule_id:
                target_rule = rule
                break
        
        if not target_rule:
            raise ValueError(f"Rule {modification.rule_id} not found")
        
        # Apply modification based on type
        if modification.modification_type == ModificationType.ADJUST_THRESHOLD:
            self._adjust_threshold(target_rule, modification.parameters)
        
        elif modification.modification_type == ModificationType.CHANGE_PRIORITY:
            target_rule['priority'] = modification.parameters['new_priority']
        
        elif modification.modification_type == ModificationType.ADD_CONDITION:
            target_rule['conditions'].append(modification.parameters['new_condition'])
        
        elif modification.modification_type == ModificationType.REMOVE_CONDITION:
            condition_index = modification.parameters['condition_index']
            if 0 <= condition_index < len(target_rule['conditions']):
                target_rule['conditions'].pop(condition_index)
        
        elif modification.modification_type == ModificationType.MODIFY_DECISION:
            target_rule['decision'].update(modification.parameters['decision_updates'])
        
        elif modification.modification_type == ModificationType.DISABLE_RULE:
            # Mark rule as disabled by setting very low priority
            target_rule['_disabled'] = True
            target_rule['priority'] = 99999
        
        elif modification.modification_type == ModificationType.ADD_BUFFER_ZONE:
            self._add_buffer_zone(modified_rules, target_rule, modification.parameters)
        
        # Re-sort rules by priority
        modified_rules['rules'] = sorted(modified_rules['rules'], 
                                        key=lambda r: r['priority'])
        
        # Store modification history
        self.modification_history.append({
            'modification': modification,
            'timestamp': self._get_timestamp()
        })
        
        return modified_rules
    
    def _adjust_threshold(self, rule: Dict, parameters: Dict):
        """Adjust threshold value in a condition."""
        condition_index = parameters.get('condition_index', 0)
        adjustment = parameters.get('adjustment', 0)
        
        if 0 <= condition_index < len(rule['conditions']):
            condition = rule['conditions'][condition_index]
            
            if isinstance(condition['value'], (int, float)):
                condition['value'] += adjustment
            elif isinstance(condition['value'], list):
                # Adjust range boundaries
                condition['value'] = [v + adjustment for v in condition['value']]
    
    def _add_buffer_zone(self, modified_rules: Dict, target_rule: Dict, parameters: Dict):
        """
        Add a buffer zone by creating an intermediate rule.
        
        This smooths sharp decision boundaries by adding an intermediate
        decision category.
        """
        # Create intermediate rule
        intermediate_rule = copy.deepcopy(target_rule)
        intermediate_rule['rule_id'] = f"{target_rule['rule_id']}_buffer"
        intermediate_rule['name'] = f"{target_rule.get('name', '')} - Buffer Zone"
        intermediate_rule['priority'] = target_rule['priority'] + 0.5  # Insert between priorities
        
        # Adjust conditions to create buffer zone
        buffer_percent = parameters.get('buffer_percent', 0.1)
        
        for condition in intermediate_rule['conditions']:
            if isinstance(condition['value'], (int, float)):
                # Create buffer zone around threshold
                original_value = condition['value']
                buffer_amount = abs(original_value * buffer_percent)
                
                if condition['operator'] in ['>', '>=']:
                    condition['value'] = original_value - buffer_amount
                elif condition['operator'] in ['<', '<=']:
                    condition['value'] = original_value + buffer_amount
        
        # Change decision to intermediate category
        intermediate_decision = parameters.get('intermediate_decision', 'review')
        intermediate_rule['decision']['outcome'] = intermediate_decision
        intermediate_rule['decision']['confidence'] *= 0.8  # Lower confidence for buffer zone
        intermediate_rule['decision']['reasoning'] = f"Buffer zone - {intermediate_rule['decision']['reasoning']}"
        
        # Add to rules list
        modified_rules['rules'].append(intermediate_rule)
    
    def simulate_impact(self, modification: RuleModification,
                       decision_executor, scenarios: List[Dict],
                       risk_scorer) -> Dict:
        """
        Simulate the impact of a modification on test scenarios.
        
        Args:
            modification: RuleModification to test
            decision_executor: DecisionExecutor instance
            scenarios: Test scenarios to evaluate
            risk_scorer: RiskScorer instance
            
        Returns:
            Dictionary comparing before and after metrics
        """
        # Import RuleEngine here to avoid circular dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from policy_engine import RuleEngine
        
        # Get baseline results with original rules
        baseline_results = decision_executor.execute_batch(scenarios, store_audit_trail=False)
        baseline_distribution = baseline_results['decision'].value_counts().to_dict()
        
        # Apply modification
        modified_rules = self.apply_modification(modification)
        
        # Create temporary modified engine
        temp_engine = RuleEngine()
        temp_engine.rules = modified_rules
        temp_engine.rule_set_name = modified_rules['rule_set_name']
        
        # Re-create executor with modified engine
        from decision_executor import DecisionExecutor
        modified_executor = DecisionExecutor(temp_engine)
        modified_results = modified_executor.execute_batch(scenarios, store_audit_trail=False)
        modified_distribution = modified_results['decision'].value_counts().to_dict()
        
        # Calculate risk scores for both
        baseline_scorer = copy.deepcopy(risk_scorer)
        baseline_coverage = baseline_scorer.score_coverage_gaps(baseline_results)
        baseline_concentration = baseline_scorer.score_decision_concentration(baseline_results)
        baseline_composite = baseline_scorer.calculate_composite_risk_score()
        
        modified_scorer = copy.deepcopy(risk_scorer)
        modified_coverage = modified_scorer.score_coverage_gaps(modified_results)
        modified_concentration = modified_scorer.score_decision_concentration(modified_results)
        modified_composite = modified_scorer.calculate_composite_risk_score()
        
        # Compare results
        impact_analysis = {
            'modification': modification,
            'baseline': {
                'decision_distribution': baseline_distribution,
                'coverage_gap_rate': baseline_coverage['coverage_gap_rate'],
                'concentration_score': baseline_concentration['concentration_score'],
                'composite_risk_score': baseline_composite['composite_risk_score'],
                'overall_severity': baseline_composite['overall_severity']
            },
            'modified': {
                'decision_distribution': modified_distribution,
                'coverage_gap_rate': modified_coverage['coverage_gap_rate'],
                'concentration_score': modified_concentration['concentration_score'],
                'composite_risk_score': modified_composite['composite_risk_score'],
                'overall_severity': modified_composite['overall_severity']
            },
            'changes': {
                'decision_shifts': self._calculate_decision_shifts(
                    baseline_distribution, modified_distribution
                ),
                'risk_delta': modified_composite['composite_risk_score'] - baseline_composite['composite_risk_score'],
                'coverage_improvement': baseline_coverage['coverage_gap_rate'] - modified_coverage['coverage_gap_rate'],
                'concentration_change': modified_concentration['concentration_score'] - baseline_concentration['concentration_score']
            },
            'recommendation': self._generate_recommendation(
                baseline_composite['composite_risk_score'],
                modified_composite['composite_risk_score']
            )
        }
        
        return impact_analysis
    
    def _calculate_decision_shifts(self, baseline: Dict, modified: Dict) -> Dict:
        """Calculate how decision distribution has shifted."""
        all_decisions = set(list(baseline.keys()) + list(modified.keys()))
        
        shifts = {}
        for decision in all_decisions:
            baseline_count = baseline.get(decision, 0)
            modified_count = modified.get(decision, 0)
            shifts[decision] = {
                'before': baseline_count,
                'after': modified_count,
                'delta': modified_count - baseline_count
            }
        
        return shifts
    
    def _generate_recommendation(self, baseline_risk: float, modified_risk: float) -> str:
        """Generate recommendation based on risk comparison."""
        delta = modified_risk - baseline_risk
        
        if delta < -0.1:
            return "✅ Recommended: This modification significantly reduces risk"
        elif delta < -0.05:
            return "✅ Recommended: This modification moderately reduces risk"
        elif delta < 0.05:
            return "⚠️ Neutral: This modification has minimal impact on risk"
        elif delta < 0.1:
            return "⚠️ Caution: This modification slightly increases risk - review trade-offs"
        else:
            return "❌ Not Recommended: This modification significantly increases risk"
    
    def suggest_modifications(self, detection_results: Dict,
                            risk_scores: Dict) -> List[RuleModification]:
        """
        Suggest rule modifications based on detected issues.
        
        Args:
            detection_results: Results from FailureDetector
            risk_scores: Risk scores from RiskScorer
            
        Returns:
            List of suggested RuleModification objects
        """
        suggestions = []
        
        # Suggest modifications for high instability
        if 'instabilities' in detection_results:
            for instability in detection_results['instabilities'][:3]:  # Top 3
                if instability['instability_score'] > 0.3:
                    # Find which rule caused instability
                    base_decision = instability['base_decision']
                    
                    # Suggest adding buffer zone
                    suggestions.append(RuleModification(
                        rule_id=f"R{len(suggestions)+1:03d}",  # Placeholder
                        modification_type=ModificationType.ADD_BUFFER_ZONE,
                        parameters={
                            'buffer_percent': 0.1,
                            'intermediate_decision': 'review'
                        },
                        description=f"Add buffer zone to reduce instability near {base_decision} boundary"
                    ))
        
        # Suggest modifications for high coverage gaps
        if risk_scores.get('coverage', {}).get('coverage_gap_rate', 0) > 0.1:
            suggestions.append(RuleModification(
                rule_id="default",
                modification_type=ModificationType.MODIFY_DECISION,
                parameters={
                    'decision_updates': {
                        'outcome': 'review',
                        'reasoning': 'No specific rule matched - requires manual review'
                    }
                },
                description="Improve default decision handling for uncovered scenarios"
            ))
        
        # Suggest modifications for high concentration
        if risk_scores.get('concentration', {}).get('concentration_score', 0) > 0.7:
            suggestions.append(RuleModification(
                rule_id="R001",  # Placeholder
                modification_type=ModificationType.ADJUST_THRESHOLD,
                parameters={
                    'condition_index': 0,
                    'adjustment': 5  # Adjust by 5 units
                },
                description="Adjust thresholds to improve decision diversity"
            ))
        
        return suggestions
    
    def export_modified_rules(self, modified_rules: Dict, filepath: str):
        """
        Export modified rules to a JSON file.
        
        Args:
            modified_rules: Modified rules dictionary
            filepath: Path to save the file
        """
        with open(filepath, 'w') as f:
            json.dump(modified_rules, f, indent=2)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def reset(self):
        """Reset to original rules and clear modification history."""
        self.modification_history = []
