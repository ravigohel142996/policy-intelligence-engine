"""
Risk & Impact Scoring Module

This module scores severity, frequency, and potential impact of failures.
Focus on non-accuracy metrics:
1. Instability scores (sensitivity to perturbations)
2. Conflict density (overlapping rule activations)
3. Decision boundary sharpness
4. Rule coverage and gaps

Design Philosophy:
- Risk != prediction error
- Focus on systemic issues, not individual misclassifications
- Quantify what could go wrong at scale
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict


class RiskScorer:
    """
    Scores risk and impact of detected failures and instabilities.
    
    Provides non-accuracy-based metrics focused on:
    - System stability
    - Rule conflict severity
    - Decision boundary quality
    - Coverage gaps
    """
    
    def __init__(self):
        """Initialize the risk scorer."""
        self.risk_scores = {}
    
    def score_instability(self, instability_reports: List[Dict]) -> Dict:
        """
        Score instability risk across scenarios.
        
        Args:
            instability_reports: List of instability reports from FailureDetector
            
        Returns:
            Dictionary with instability risk metrics
        """
        if not instability_reports:
            return {
                'overall_instability_risk': 0.0,
                'max_instability_score': 0.0,
                'unstable_scenario_count': 0,
                'severity': 'low'
            }
        
        instability_scores = [r['instability_score'] for r in instability_reports]
        
        overall_risk = np.mean(instability_scores)
        max_risk = np.max(instability_scores)
        
        # Determine severity level
        if max_risk > 0.5:
            severity = 'critical'
        elif max_risk > 0.3:
            severity = 'high'
        elif max_risk > 0.1:
            severity = 'medium'
        else:
            severity = 'low'
        
        risk_metrics = {
            'overall_instability_risk': float(overall_risk),
            'max_instability_score': float(max_risk),
            'unstable_scenario_count': len(instability_reports),
            'severity': severity,
            'high_risk_scenarios': [
                r['scenario_id'] for r in instability_reports 
                if r['instability_score'] > 0.3
            ]
        }
        
        self.risk_scores['instability'] = risk_metrics
        return risk_metrics
    
    def score_conflict_density(self, results_df: pd.DataFrame,
                              boundaries: List[Dict]) -> Dict:
        """
        Score conflict density - how many decision boundaries exist.
        
        High conflict density indicates many rule interactions and
        potential for unexpected behavior.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            boundaries: List of decision boundaries
            
        Returns:
            Dictionary with conflict density metrics
        """
        total_scenarios = len(results_df)
        
        if total_scenarios == 0:
            return {'conflict_density': 0.0, 'severity': 'low'}
        
        # Count unique rule transitions
        rule_transitions = set()
        for boundary in boundaries:
            rule_before = boundary.get('rule_before')
            rule_after = boundary.get('rule_after')
            # Only count if both rules are present
            if rule_before and rule_after:
                rule_pair = tuple(sorted([str(rule_before), str(rule_after)]))
                rule_transitions.add(rule_pair)
        
        # Calculate density
        num_boundaries = len(boundaries)
        conflict_density = num_boundaries / total_scenarios
        
        # Calculate boundary sharpness - average gap size
        if boundaries:
            avg_gap = np.mean([b['value_gap'] for b in boundaries])
            gap_variance = np.var([b['value_gap'] for b in boundaries])
        else:
            avg_gap = 0
            gap_variance = 0
        
        # Determine severity
        if conflict_density > 0.3:
            severity = 'critical'
        elif conflict_density > 0.15:
            severity = 'high'
        elif conflict_density > 0.05:
            severity = 'medium'
        else:
            severity = 'low'
        
        conflict_metrics = {
            'conflict_density': float(conflict_density),
            'total_boundaries': num_boundaries,
            'unique_rule_transitions': len(rule_transitions),
            'avg_boundary_gap': float(avg_gap),
            'boundary_gap_variance': float(gap_variance),
            'severity': severity
        }
        
        self.risk_scores['conflict'] = conflict_metrics
        return conflict_metrics
    
    def score_coverage_gaps(self, results_df: pd.DataFrame) -> Dict:
        """
        Score rule coverage gaps - scenarios with no matching rules.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            
        Returns:
            Dictionary with coverage gap metrics
        """
        total_scenarios = len(results_df)
        
        if total_scenarios == 0:
            return {'coverage_gap_rate': 0.0, 'severity': 'low'}
        
        # Count scenarios with no rule match
        no_match = results_df[results_df['rule_id'].isna()]
        gap_count = len(no_match)
        gap_rate = gap_count / total_scenarios
        
        # Analyze distribution of unmatched scenarios
        if gap_count > 0:
            # Get feature statistics for unmatched scenarios
            feature_cols = [col for col in results_df.columns if col.startswith('feature_')]
            gap_feature_stats = {}
            
            for col in feature_cols:
                if results_df[col].dtype in ['int64', 'float64']:
                    gap_feature_stats[col] = {
                        'mean': float(no_match[col].mean()),
                        'std': float(no_match[col].std()),
                        'min': float(no_match[col].min()),
                        'max': float(no_match[col].max())
                    }
        else:
            gap_feature_stats = {}
        
        # Determine severity
        if gap_rate > 0.2:
            severity = 'critical'
        elif gap_rate > 0.1:
            severity = 'high'
        elif gap_rate > 0.05:
            severity = 'medium'
        else:
            severity = 'low'
        
        coverage_metrics = {
            'coverage_gap_rate': float(gap_rate),
            'scenarios_without_match': gap_count,
            'total_scenarios': total_scenarios,
            'gap_feature_statistics': gap_feature_stats,
            'severity': severity
        }
        
        self.risk_scores['coverage'] = coverage_metrics
        return coverage_metrics
    
    def score_decision_concentration(self, results_df: pd.DataFrame) -> Dict:
        """
        Score decision concentration - whether decisions are evenly distributed.
        
        High concentration (all scenarios leading to same decision) may indicate
        overly restrictive or permissive rules.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            
        Returns:
            Dictionary with concentration metrics
        """
        if len(results_df) == 0:
            return {'concentration_score': 0.0, 'severity': 'low'}
        
        # Calculate decision distribution
        decision_dist = results_df['decision'].value_counts(normalize=True)
        
        # Calculate Gini coefficient for concentration
        decision_props = sorted(decision_dist.values, reverse=True)
        n = len(decision_props)
        
        if n == 1:
            gini = 1.0  # Complete concentration
        else:
            cumsum = np.cumsum(decision_props)
            gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
        
        # Determine severity
        if gini > 0.8:
            severity = 'critical'
            interpretation = 'Extreme concentration - nearly all scenarios lead to same decision'
        elif gini > 0.6:
            severity = 'high'
            interpretation = 'High concentration - limited decision diversity'
        elif gini > 0.4:
            severity = 'medium'
            interpretation = 'Moderate concentration'
        else:
            severity = 'low'
            interpretation = 'Well-distributed decisions'
        
        concentration_metrics = {
            'concentration_score': float(gini),
            'decision_distribution': decision_dist.to_dict(),
            'unique_decisions': len(decision_dist),
            'severity': severity,
            'interpretation': interpretation
        }
        
        self.risk_scores['concentration'] = concentration_metrics
        return concentration_metrics
    
    def score_confidence_variance(self, results_df: pd.DataFrame) -> Dict:
        """
        Score confidence variance across decisions.
        
        High variance indicates inconsistent confidence in decisions,
        potentially revealing unclear or conflicting rules.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            
        Returns:
            Dictionary with confidence variance metrics
        """
        if len(results_df) == 0 or 'confidence' not in results_df.columns:
            return {'confidence_variance': 0.0, 'severity': 'low'}
        
        confidence_mean = results_df['confidence'].mean()
        confidence_std = results_df['confidence'].std()
        confidence_min = results_df['confidence'].min()
        
        # Low confidence scenarios
        low_confidence_count = len(results_df[results_df['confidence'] < 0.5])
        low_confidence_rate = low_confidence_count / len(results_df)
        
        # Determine severity based on variance and low confidence rate
        if confidence_std > 0.3 or low_confidence_rate > 0.3:
            severity = 'high'
        elif confidence_std > 0.2 or low_confidence_rate > 0.15:
            severity = 'medium'
        else:
            severity = 'low'
        
        confidence_metrics = {
            'confidence_mean': float(confidence_mean),
            'confidence_std': float(confidence_std),
            'confidence_min': float(confidence_min),
            'low_confidence_rate': float(low_confidence_rate),
            'low_confidence_count': int(low_confidence_count),
            'severity': severity
        }
        
        self.risk_scores['confidence'] = confidence_metrics
        return confidence_metrics
    
    def calculate_composite_risk_score(self) -> Dict:
        """
        Calculate composite risk score combining all risk factors.
        
        Returns:
            Dictionary with composite risk assessment
        """
        if not self.risk_scores:
            return {
                'composite_risk_score': 0.0,
                'overall_severity': 'low',
                'risk_factors': {}
            }
        
        # Weight different risk factors
        weights = {
            'instability': 0.35,
            'conflict': 0.25,
            'coverage': 0.20,
            'concentration': 0.10,
            'confidence': 0.10
        }
        
        severity_scores = {
            'low': 0.25,
            'medium': 0.50,
            'high': 0.75,
            'critical': 1.0
        }
        
        # Calculate weighted composite score
        composite_score = 0.0
        risk_breakdown = {}
        
        for risk_type, weight in weights.items():
            if risk_type in self.risk_scores:
                severity = self.risk_scores[risk_type].get('severity', 'low')
                score = severity_scores[severity]
                composite_score += weight * score
                risk_breakdown[risk_type] = {
                    'severity': severity,
                    'weight': weight,
                    'contribution': weight * score
                }
        
        # Determine overall severity
        if composite_score > 0.75:
            overall_severity = 'critical'
        elif composite_score > 0.50:
            overall_severity = 'high'
        elif composite_score > 0.25:
            overall_severity = 'medium'
        else:
            overall_severity = 'low'
        
        return {
            'composite_risk_score': float(composite_score),
            'overall_severity': overall_severity,
            'risk_breakdown': risk_breakdown,
            'detailed_scores': self.risk_scores
        }
    
    def generate_risk_report(self) -> str:
        """
        Generate human-readable risk report.
        
        Returns:
            Formatted risk report string
        """
        composite = self.calculate_composite_risk_score()
        
        report = []
        report.append("=" * 60)
        report.append("POLICY INTELLIGENCE ENGINE - RISK ASSESSMENT REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Overall Risk Level: {composite['overall_severity'].upper()}")
        report.append(f"Composite Risk Score: {composite['composite_risk_score']:.2f} / 1.00")
        report.append("")
        report.append("Risk Factor Breakdown:")
        report.append("-" * 60)
        
        for risk_type, details in composite.get('risk_breakdown', {}).items():
            report.append(f"\n{risk_type.upper()}:")
            report.append(f"  Severity: {details['severity']}")
            report.append(f"  Contribution to Overall Risk: {details['contribution']:.3f}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def export_risk_scores(self, filepath: str):
        """
        Export risk scores to JSON file.
        
        Args:
            filepath: Path to save risk scores
        """
        import json
        
        composite = self.calculate_composite_risk_score()
        
        with open(filepath, 'w') as f:
            json.dump(composite, f, indent=2)
