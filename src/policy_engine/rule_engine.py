"""
Rule Engine Module

This module implements a deterministic rule execution engine that:
1. Loads and validates decision rules from JSON/YAML files
2. Evaluates conditions against input scenarios
3. Tracks rule activation paths for explainability
4. Returns deterministic decisions with full audit trails

Design Philosophy:
- No ML/predictions - purely deterministic logic
- Complete transparency - every decision is traceable
- Designed for stress-testing, not production deployment
"""

import json
import yaml
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import jsonschema


class RuleEngine:
    """
    Deterministic rule execution engine for policy evaluation.
    
    This engine evaluates structured rules against input scenarios
    and returns decisions with complete audit trails showing which
    rules were activated and why.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize the rule engine.
        
        Args:
            rules_path: Path to rules file (JSON or YAML). If None, rules must be loaded separately.
        """
        self.rules = None
        self.rule_set_name = None
        self.schema = self._load_schema()
        
        if rules_path:
            self.load_rules(rules_path)
    
    def _load_schema(self) -> Dict:
        """Load the JSON schema for rule validation."""
        schema_path = Path(__file__).parent.parent.parent / "config" / "rule_schema.json"
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    def load_rules(self, rules_path: str) -> None:
        """
        Load and validate rules from a file.
        
        Args:
            rules_path: Path to JSON or YAML file containing rules
            
        Raises:
            ValueError: If rules don't match schema or file format is invalid
        """
        rules_path = Path(rules_path)
        
        # Load rules based on file extension
        with open(rules_path, 'r') as f:
            if rules_path.suffix.lower() in ['.yaml', '.yml']:
                rules_data = yaml.safe_load(f)
            elif rules_path.suffix.lower() == '.json':
                rules_data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {rules_path.suffix}")
        
        # Validate against schema
        try:
            jsonschema.validate(instance=rules_data, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Rule validation failed: {e.message}")
        
        # Sort rules by priority
        rules_data['rules'] = sorted(rules_data['rules'], key=lambda r: r['priority'])
        
        self.rules = rules_data
        self.rule_set_name = rules_data['rule_set_name']
    
    def evaluate_condition(self, condition: Dict, scenario: Dict) -> bool:
        """
        Evaluate a single condition against a scenario.
        
        Args:
            condition: Condition definition with feature, operator, value
            scenario: Input scenario with feature values
            
        Returns:
            True if condition is met, False otherwise
        """
        feature = condition['feature']
        operator = condition['operator']
        expected_value = condition['value']
        
        # Get actual value from scenario
        if feature not in scenario:
            return False
        
        actual_value = scenario[feature]
        
        # Evaluate based on operator
        if operator == '==':
            return actual_value == expected_value
        elif operator == '!=':
            return actual_value != expected_value
        elif operator == '>':
            return actual_value > expected_value
        elif operator == '<':
            return actual_value < expected_value
        elif operator == '>=':
            return actual_value >= expected_value
        elif operator == '<=':
            return actual_value <= expected_value
        elif operator == 'in':
            return actual_value in expected_value
        elif operator == 'not_in':
            return actual_value not in expected_value
        elif operator == 'between':
            # expected_value should be [min, max]
            return expected_value[0] <= actual_value <= expected_value[1]
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def evaluate_rule(self, rule: Dict, scenario: Dict) -> Tuple[bool, List[Dict]]:
        """
        Evaluate all conditions in a rule.
        
        Args:
            rule: Rule definition with conditions
            scenario: Input scenario
            
        Returns:
            Tuple of (rule_matched, condition_results)
            condition_results contains details of each condition evaluation
        """
        conditions = rule['conditions']
        condition_results = []
        
        # Track evaluation state
        current_result = None
        
        for i, condition in enumerate(conditions):
            # Evaluate this condition
            result = self.evaluate_condition(condition, scenario)
            
            condition_results.append({
                'feature': condition['feature'],
                'operator': condition['operator'],
                'expected': condition['value'],
                'actual': scenario.get(condition['feature']),
                'result': result
            })
            
            # Apply logical operator
            logical = condition.get('logical', 'AND')
            
            if current_result is None:
                current_result = result
            elif logical == 'AND':
                current_result = current_result and result
            elif logical == 'OR':
                current_result = current_result or result
        
        return current_result, condition_results
    
    def execute(self, scenario: Dict) -> Dict:
        """
        Execute rules against a scenario and return decision with audit trail.
        
        Args:
            scenario: Dictionary containing feature values
            
        Returns:
            Dictionary containing:
            - decision: The final decision outcome
            - matched_rule: The rule that matched (if any)
            - rule_id: ID of matched rule
            - confidence: Confidence level
            - reasoning: Explanation
            - audit_trail: Complete evaluation history
        """
        if self.rules is None:
            raise RuntimeError("No rules loaded. Call load_rules() first.")
        
        audit_trail = {
            'scenario': scenario,
            'rules_evaluated': [],
            'rule_set_name': self.rule_set_name
        }
        
        # Evaluate rules in priority order
        for rule in self.rules['rules']:
            matched, condition_results = self.evaluate_rule(rule, scenario)
            
            audit_trail['rules_evaluated'].append({
                'rule_id': rule['rule_id'],
                'rule_name': rule.get('name', ''),
                'priority': rule['priority'],
                'matched': matched,
                'conditions': condition_results
            })
            
            # If rule matches and stop_on_match is True, return decision
            if matched:
                stop_on_match = rule.get('stop_on_match', True)
                decision = rule['decision']
                
                result = {
                    'decision': decision['outcome'],
                    'matched_rule': rule,
                    'rule_id': rule['rule_id'],
                    'confidence': decision.get('confidence', 1.0),
                    'reasoning': decision.get('reasoning', ''),
                    'audit_trail': audit_trail
                }
                
                if stop_on_match:
                    return result
        
        # No rules matched - return default decision
        default = self.rules.get('default_decision', {
            'outcome': 'no_decision',
            'reasoning': 'No rules matched'
        })
        
        return {
            'decision': default['outcome'],
            'matched_rule': None,
            'rule_id': None,
            'confidence': 0.0,
            'reasoning': default.get('reasoning', 'No rules matched'),
            'audit_trail': audit_trail
        }
    
    def batch_execute(self, scenarios: List[Dict]) -> List[Dict]:
        """
        Execute rules against multiple scenarios.
        
        Args:
            scenarios: List of scenario dictionaries
            
        Returns:
            List of decision results
        """
        return [self.execute(scenario) for scenario in scenarios]
    
    def get_rule_summary(self) -> Dict:
        """
        Get summary statistics about the loaded rule set.
        
        Returns:
            Dictionary with rule set statistics
        """
        if self.rules is None:
            return {}
        
        return {
            'rule_set_name': self.rule_set_name,
            'version': self.rules.get('version'),
            'total_rules': len(self.rules['rules']),
            'unique_features': len(set(
                cond['feature'] 
                for rule in self.rules['rules'] 
                for cond in rule['conditions']
            )),
            'decision_outcomes': list(set(
                rule['decision']['outcome'] 
                for rule in self.rules['rules']
            ))
        }


def load_rule_engine(rules_path: str) -> RuleEngine:
    """
    Convenience function to create and load a rule engine.
    
    Args:
        rules_path: Path to rules file
        
    Returns:
        Initialized RuleEngine instance
    """
    engine = RuleEngine(rules_path)
    return engine
