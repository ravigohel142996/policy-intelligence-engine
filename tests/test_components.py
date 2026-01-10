"""
Simple test script to validate all core components work correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_rule_engine():
    """Test Rule Engine."""
    print("Testing Rule Engine...", end=" ")
    from policy_engine import RuleEngine
    
    rules_path = Path(__file__).parent.parent / "examples" / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    
    # Test single scenario
    scenario = {
        'credit_score': 720,
        'annual_income': 80000,
        'age': 35,
        'debt_to_income': 0.25
    }
    
    result = engine.execute(scenario)
    assert result['decision'] is not None
    assert 'audit_trail' in result
    
    print("✓")


def test_scenario_generator():
    """Test Scenario Generator."""
    print("Testing Scenario Generator...", end=" ")
    from scenario_generator import ScenarioGenerator, FeatureSpec
    
    specs = [
        FeatureSpec(name='feature1', type='continuous', range=(0, 100)),
        FeatureSpec(name='feature2', type='discrete', range=(1, 10)),
        FeatureSpec(name='feature3', type='categorical', values=['A', 'B', 'C'])
    ]
    
    generator = ScenarioGenerator(specs, random_seed=42)
    scenarios = generator.generate(100)
    
    assert len(scenarios) == 100
    assert all('feature1' in s for s in scenarios)
    
    print("✓")


def test_decision_executor():
    """Test Decision Executor."""
    print("Testing Decision Executor...", end=" ")
    from policy_engine import RuleEngine
    from scenario_generator import ScenarioGenerator, FeatureSpec
    from decision_executor import DecisionExecutor
    
    rules_path = Path(__file__).parent.parent / "examples" / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    
    specs = [
        FeatureSpec(name='credit_score', type='continuous', range=(300, 850)),
        FeatureSpec(name='annual_income', type='continuous', range=(20000, 150000)),
        FeatureSpec(name='age', type='discrete', range=(18, 70)),
        FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 0.8))
    ]
    
    generator = ScenarioGenerator(specs, random_seed=42)
    scenarios = generator.generate(50)
    
    executor = DecisionExecutor(engine)
    results = executor.execute_batch(scenarios, store_audit_trail=False)
    
    assert len(results) == 50
    assert 'decision' in results.columns
    
    print("✓")


def test_failure_detector():
    """Test Failure Detector."""
    print("Testing Failure Detector...", end=" ")
    from policy_engine import RuleEngine
    from scenario_generator import ScenarioGenerator, FeatureSpec
    from decision_executor import DecisionExecutor
    from failure_detector import FailureDetector
    
    rules_path = Path(__file__).parent.parent / "examples" / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    
    specs = [
        FeatureSpec(name='credit_score', type='continuous', range=(300, 850)),
        FeatureSpec(name='annual_income', type='continuous', range=(20000, 150000)),
        FeatureSpec(name='age', type='discrete', range=(18, 70)),
        FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 0.8))
    ]
    
    generator = ScenarioGenerator(specs, random_seed=42)
    scenarios = generator.generate(100)
    
    executor = DecisionExecutor(engine)
    results = executor.execute_batch(scenarios, store_audit_trail=False)
    
    detector = FailureDetector()
    results_with_anomalies = detector.detect_anomalies(results, contamination=0.1)
    
    assert 'is_anomaly' in results_with_anomalies.columns
    assert 'anomaly_score' in results_with_anomalies.columns
    
    print("✓")


def test_risk_scorer():
    """Test Risk Scorer."""
    print("Testing Risk Scorer...", end=" ")
    from policy_engine import RuleEngine
    from scenario_generator import ScenarioGenerator, FeatureSpec
    from decision_executor import DecisionExecutor
    from risk_scoring import RiskScorer
    
    rules_path = Path(__file__).parent.parent / "examples" / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    
    specs = [
        FeatureSpec(name='credit_score', type='continuous', range=(300, 850)),
        FeatureSpec(name='annual_income', type='continuous', range=(20000, 150000)),
        FeatureSpec(name='age', type='discrete', range=(18, 70)),
        FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 0.8))
    ]
    
    generator = ScenarioGenerator(specs, random_seed=42)
    scenarios = generator.generate(100)
    
    executor = DecisionExecutor(engine)
    results = executor.execute_batch(scenarios, store_audit_trail=False)
    
    scorer = RiskScorer()
    coverage = scorer.score_coverage_gaps(results)
    concentration = scorer.score_decision_concentration(results)
    
    assert 'coverage_gap_rate' in coverage
    assert 'concentration_score' in concentration
    
    composite = scorer.calculate_composite_risk_score()
    assert 'composite_risk_score' in composite
    assert 'overall_severity' in composite
    
    print("✓")


def test_explainability():
    """Test Explainability Engine."""
    print("Testing Explainability Engine...", end=" ")
    from policy_engine import RuleEngine
    from scenario_generator import ScenarioGenerator, FeatureSpec
    from decision_executor import DecisionExecutor
    from explainability import ExplainabilityEngine
    
    rules_path = Path(__file__).parent.parent / "examples" / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    
    executor = DecisionExecutor(engine)
    explainer = ExplainabilityEngine(engine, executor)
    
    # Test boundary explanation
    boundary = {
        'feature': 'credit_score',
        'value_before': 599,
        'value_after': 601,
        'value_gap': 2,
        'rule_before': 'R003',
        'rule_after': 'R005',
        'decision_before': 'reject',
        'decision_after': 'review'
    }
    
    explanation = explainer.explain_boundary(boundary)
    
    assert 'summary' in explanation
    assert 'suggestions' in explanation
    
    print("✓")


def main():
    """Run all tests."""
    print("=" * 60)
    print("POLICY INTELLIGENCE ENGINE - Component Tests")
    print("=" * 60)
    print()
    
    try:
        test_rule_engine()
        test_scenario_generator()
        test_decision_executor()
        test_failure_detector()
        test_risk_scorer()
        test_explainability()
        
        print()
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
