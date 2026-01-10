"""
Explainability Engine Module

This module explains detected failures with:
1. Which rules caused the failure
2. Why it happened (root cause analysis)
3. What small rule changes could reduce risk

Design Philosophy:
- No black-box explanations
- Every failure has a clear causal path
- Actionable recommendations for rule improvements
- Human-readable explanations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


class ExplainabilityEngine:
    """
    Generates human-readable explanations for detected failures and instabilities.
    
    For each detected issue, explains:
    - Root cause (which rules/conditions)
    - Contributing factors
    - Suggested rule modifications
    """
    
    def __init__(self, rule_engine, decision_executor):
        """
        Initialize the explainability engine.
        
        Args:
            rule_engine: RuleEngine instance
            decision_executor: DecisionExecutor instance
        """
        self.rule_engine = rule_engine
        self.decision_executor = decision_executor
        self.explanations = []
    
    def explain_anomaly(self, scenario: Dict, decision_result: Dict) -> Dict:
        """
        Explain why a scenario was flagged as anomalous.
        
        Args:
            scenario: The anomalous scenario
            decision_result: Decision result from rule engine
            
        Returns:
            Dictionary with explanation details
        """
        explanation = {
            'scenario': scenario,
            'decision': decision_result['decision'],
            'matched_rule': decision_result['rule_id'],
            'explanation_type': 'anomaly',
            'root_cause': []
        }
        
        # Analyze audit trail
        audit_trail = decision_result.get('audit_trail', {})
        
        # Check which conditions were evaluated
        rules_evaluated = audit_trail.get('rules_evaluated', [])
        
        for rule_eval in rules_evaluated:
            if rule_eval['matched']:
                # Explain why this rule matched
                conditions = rule_eval['conditions']
                
                for cond in conditions:
                    if cond['result']:
                        explanation['root_cause'].append({
                            'type': 'condition_match',
                            'feature': cond['feature'],
                            'operator': cond['operator'],
                            'expected': cond['expected'],
                            'actual': cond['actual'],
                            'description': f"{cond['feature']} {cond['operator']} {cond['expected']}"
                        })
        
        # Generate human-readable summary
        explanation['summary'] = self._generate_anomaly_summary(scenario, decision_result)
        
        # Suggest modifications
        explanation['suggestions'] = self._suggest_rule_modifications(scenario, decision_result)
        
        return explanation
    
    def explain_instability(self, instability_report: Dict) -> Dict:
        """
        Explain why a scenario exhibits decision instability.
        
        Args:
            instability_report: Instability report from FailureDetector
            
        Returns:
            Dictionary with explanation details
        """
        base_scenario = instability_report['base_scenario']
        decision_changes = instability_report['decision_changes']
        
        explanation = {
            'base_scenario': base_scenario,
            'base_decision': instability_report['base_decision'],
            'instability_score': instability_report['instability_score'],
            'explanation_type': 'instability',
            'root_cause': []
        }
        
        # Analyze what changed in perturbed scenarios
        affected_features = set()
        rule_transitions = set()
        
        for change in decision_changes:
            # Identify which features caused the change
            perturbed = change['perturbed_scenario']
            
            for feature, base_value in base_scenario.items():
                perturbed_value = perturbed.get(feature)
                if base_value != perturbed_value:
                    affected_features.add(feature)
                    
                    explanation['root_cause'].append({
                        'type': 'feature_sensitivity',
                        'feature': feature,
                        'base_value': base_value,
                        'perturbed_value': perturbed_value,
                        'base_decision': change['original_decision'],
                        'new_decision': change['new_decision'],
                        'distance': change['distance']
                    })
            
            # Track rule transitions
            rule_pair = (change['original_rule'], change['new_rule'])
            rule_transitions.add(rule_pair)
        
        # Generate summary
        explanation['affected_features'] = list(affected_features)
        explanation['rule_transitions'] = list(rule_transitions)
        explanation['summary'] = self._generate_instability_summary(instability_report, affected_features)
        
        # Suggest modifications
        explanation['suggestions'] = self._suggest_stability_improvements(
            instability_report, affected_features
        )
        
        return explanation
    
    def explain_boundary(self, boundary: Dict) -> Dict:
        """
        Explain a decision boundary between two rules.
        
        Args:
            boundary: Boundary information from DecisionExecutor
            
        Returns:
            Dictionary with explanation details
        """
        explanation = {
            'feature': boundary['feature'],
            'boundary_point': (boundary['value_before'] + boundary['value_after']) / 2,
            'explanation_type': 'boundary',
            'root_cause': []
        }
        
        # Explain the transition
        explanation['root_cause'].append({
            'type': 'rule_transition',
            'feature': boundary['feature'],
            'value_before': boundary['value_before'],
            'value_after': boundary['value_after'],
            'gap': boundary['value_gap'],
            'rule_before': boundary['rule_before'],
            'rule_after': boundary['rule_after'],
            'decision_before': boundary['decision_before'],
            'decision_after': boundary['decision_after']
        })
        
        # Generate summary
        explanation['summary'] = (
            f"Decision boundary detected on feature '{boundary['feature']}'. "
            f"When {boundary['feature']} changes from {boundary['value_before']:.3f} "
            f"to {boundary['value_after']:.3f} (gap: {boundary['value_gap']:.3f}), "
            f"the decision changes from '{boundary['decision_before']}' "
            f"(rule {boundary['rule_before']}) to '{boundary['decision_after']}' "
            f"(rule {boundary['rule_after']})."
        )
        
        # Assess boundary sharpness
        if boundary['value_gap'] < 0.01:
            risk_level = 'high'
            risk_description = 'Very sharp boundary - minimal input change causes decision flip'
        elif boundary['value_gap'] < 0.05:
            risk_level = 'medium'
            risk_description = 'Moderately sharp boundary'
        else:
            risk_level = 'low'
            risk_description = 'Gradual boundary'
        
        explanation['risk_level'] = risk_level
        explanation['risk_description'] = risk_description
        
        # Suggest modifications
        explanation['suggestions'] = [{
            'modification': 'add_intermediate_rule',
            'description': (
                f"Consider adding an intermediate rule or decision category "
                f"between {boundary['value_before']:.3f} and {boundary['value_after']:.3f} "
                f"to smooth the transition."
            )
        }]
        
        return explanation
    
    def explain_conflict(self, conflict: Dict) -> Dict:
        """
        Explain a rule conflict where similar scenarios get different decisions.
        
        Args:
            conflict: Conflict information from DecisionExecutor
            
        Returns:
            Dictionary with explanation details
        """
        explanation = {
            'scenario1': conflict['scenario1'],
            'scenario2': conflict['scenario2'],
            'similarity_score': conflict['similarity_score'],
            'explanation_type': 'conflict',
            'root_cause': []
        }
        
        # Find differences between scenarios
        differences = []
        for key in conflict['scenario1'].keys():
            val1 = conflict['scenario1'][key]
            val2 = conflict['scenario2'].get(key)
            
            if val1 != val2:
                differences.append({
                    'feature': key,
                    'value1': val1,
                    'value2': val2,
                    'relative_diff': abs(val1 - val2) / max(abs(val1), abs(val2), 1e-10)
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float))
                    else 1.0
                })
        
        explanation['differences'] = differences
        explanation['root_cause'].append({
            'type': 'rule_conflict',
            'rule1': conflict['rule1'],
            'rule2': conflict['rule2'],
            'decision1': conflict['decision1'],
            'decision2': conflict['decision2']
        })
        
        # Generate summary
        explanation['summary'] = (
            f"Rule conflict detected: Two similar scenarios (similarity: {conflict['similarity_score']:.2f}) "
            f"lead to different decisions ('{conflict['decision1']}' vs '{conflict['decision2']}'). "
            f"This is caused by rules {conflict['rule1']} and {conflict['rule2']}. "
            f"Key differences: {', '.join([d['feature'] for d in differences[:3]])}."
        )
        
        # Suggest modifications
        explanation['suggestions'] = self._suggest_conflict_resolution(conflict, differences)
        
        return explanation
    
    def _generate_anomaly_summary(self, scenario: Dict, decision_result: Dict) -> str:
        """Generate human-readable summary for anomaly."""
        rule_id = decision_result['rule_id']
        decision = decision_result['decision']
        confidence = decision_result['confidence']
        
        return (
            f"This scenario was flagged as anomalous. "
            f"It was matched by rule {rule_id} leading to decision '{decision}' "
            f"with confidence {confidence:.2f}. "
            f"The scenario's feature values are unusual compared to typical patterns."
        )
    
    def _generate_instability_summary(self, report: Dict, affected_features: set) -> str:
        """Generate human-readable summary for instability."""
        score = report['instability_score']
        num_changes = len(report['decision_changes'])
        
        features_str = ', '.join(list(affected_features)[:3])
        if len(affected_features) > 3:
            features_str += f' and {len(affected_features) - 3} more'
        
        return (
            f"This scenario exhibits high decision instability (score: {score:.2f}). "
            f"Small perturbations in features ({features_str}) caused the decision to change "
            f"in {num_changes} out of {report['num_perturbations']} test cases. "
            f"This suggests the scenario is near a sensitive decision boundary."
        )
    
    def _suggest_rule_modifications(self, scenario: Dict, decision_result: Dict) -> List[Dict]:
        """Suggest modifications to reduce anomaly impact."""
        suggestions = []
        
        # Suggest adding explicit handling
        suggestions.append({
            'type': 'add_explicit_rule',
            'priority': 'high',
            'description': (
                f"Consider adding an explicit rule to handle scenarios similar to this anomaly. "
                f"This would make the system's behavior more predictable in edge cases."
            ),
            'action': 'Create a new rule with higher priority that explicitly handles these edge cases'
        })
        
        # Suggest broadening existing rule
        if decision_result['rule_id']:
            suggestions.append({
                'type': 'broaden_existing_rule',
                'priority': 'medium',
                'rule_id': decision_result['rule_id'],
                'description': (
                    f"Consider broadening the conditions in rule {decision_result['rule_id']} "
                    f"to cover this anomalous case."
                ),
                'action': f'Adjust threshold values in rule {decision_result["rule_id"]}'
            })
        
        return suggestions
    
    def _suggest_stability_improvements(self, report: Dict, affected_features: set) -> List[Dict]:
        """Suggest modifications to improve stability."""
        suggestions = []
        
        # Suggest adding buffer zones
        suggestions.append({
            'type': 'add_buffer_zone',
            'priority': 'high',
            'affected_features': list(affected_features),
            'description': (
                f"Add buffer zones or intermediate decision categories around the boundaries "
                f"of {', '.join(list(affected_features)[:3])} to reduce sensitivity."
            ),
            'action': 'Introduce intermediate rules or modify thresholds to create smoother transitions'
        })
        
        # Suggest reducing rule priority conflicts
        if len(report['decision_changes']) > 0:
            rules_involved = set(c['original_rule'] for c in report['decision_changes'])
            rules_involved.add(report['decision_changes'][0]['new_rule'])
            
            suggestions.append({
                'type': 'review_rule_priorities',
                'priority': 'medium',
                'rules_involved': list(rules_involved),
                'description': (
                    f"Review the priority and overlap of rules {', '.join(map(str, rules_involved))}. "
                    f"They may have conflicting conditions causing instability."
                ),
                'action': 'Adjust rule priorities or refine conditions to reduce overlap'
            })
        
        return suggestions
    
    def _suggest_conflict_resolution(self, conflict: Dict, differences: List[Dict]) -> List[Dict]:
        """Suggest modifications to resolve conflicts."""
        suggestions = []
        
        # Suggest consolidating rules
        suggestions.append({
            'type': 'consolidate_rules',
            'priority': 'high',
            'rules': [conflict['rule1'], conflict['rule2']],
            'description': (
                f"Rules {conflict['rule1']} and {conflict['rule2']} produce conflicting decisions "
                f"for similar scenarios. Consider consolidating them into a single rule with "
                f"clearer conditions."
            ),
            'action': f'Merge or refactor rules {conflict["rule1"]} and {conflict["rule2"]}'
        })
        
        # Suggest clarifying decision boundaries
        if differences:
            key_feature = differences[0]['feature']
            suggestions.append({
                'type': 'clarify_boundary',
                'priority': 'medium',
                'feature': key_feature,
                'description': (
                    f"The feature '{key_feature}' appears to be the main differentiator. "
                    f"Clarify the decision boundary for this feature to ensure consistent decisions."
                ),
                'action': f'Add explicit conditions on {key_feature} to separate the rules clearly'
            })
        
        return suggestions
    
    def generate_explanation_report(self, explanations: List[Dict]) -> str:
        """
        Generate comprehensive explanation report.
        
        Args:
            explanations: List of explanation dictionaries
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        report.append("POLICY INTELLIGENCE ENGINE - EXPLANATION REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Group by explanation type
        by_type = {}
        for exp in explanations:
            exp_type = exp.get('explanation_type', 'unknown')
            if exp_type not in by_type:
                by_type[exp_type] = []
            by_type[exp_type].append(exp)
        
        # Report each type
        for exp_type, exps in by_type.items():
            report.append(f"\n{exp_type.upper()} EXPLANATIONS ({len(exps)} found)")
            report.append("-" * 70)
            
            for i, exp in enumerate(exps[:5], 1):  # Show top 5
                report.append(f"\n{i}. {exp.get('summary', 'No summary available')}")
                
                # Show suggestions
                suggestions = exp.get('suggestions', [])
                if suggestions:
                    report.append("\n   Suggestions:")
                    for sug in suggestions[:2]:  # Top 2 suggestions
                        report.append(f"   - [{sug.get('priority', 'low').upper()}] {sug.get('description', '')}")
            
            if len(exps) > 5:
                report.append(f"\n   ... and {len(exps) - 5} more {exp_type} cases")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def batch_explain(self, detection_results: Dict) -> List[Dict]:
        """
        Generate explanations for all detected issues.
        
        Args:
            detection_results: Results from FailureDetector
            
        Returns:
            List of explanation dictionaries
        """
        explanations = []
        
        # Explain instabilities
        if 'instabilities' in detection_results:
            for report in detection_results['instabilities']:
                exp = self.explain_instability(report)
                explanations.append(exp)
        
        # Additional explanation types can be added here
        
        self.explanations = explanations
        return explanations
