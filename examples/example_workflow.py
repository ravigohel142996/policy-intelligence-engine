"""
Example usage of Policy Intelligence Engine

This script demonstrates a complete workflow:
1. Load rules
2. Generate scenarios
3. Execute decisions
4. Detect failures
5. Score risks
6. Generate explanations
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from policy_engine import RuleEngine
from scenario_generator import ScenarioGenerator, FeatureSpec, ScenarioType
from decision_executor import DecisionExecutor
from failure_detector import FailureDetector
from risk_scoring import RiskScorer
from explainability import ExplainabilityEngine
from policy_repair import PolicyRepairEngine, RuleModification, ModificationType


def main():
    print("=" * 70)
    print("POLICY INTELLIGENCE ENGINE - Example Workflow")
    print("=" * 70)
    print()
    
    # Step 1: Load Rules
    print("Step 1: Loading rules...")
    rules_path = Path(__file__).parent / "credit_risk_rules.json"
    engine = RuleEngine(str(rules_path))
    summary = engine.get_rule_summary()
    print(f"✓ Loaded rule set: {summary['rule_set_name']}")
    print(f"  - Total rules: {summary['total_rules']}")
    print(f"  - Features: {summary['unique_features']}")
    print()
    
    # Step 2: Generate Scenarios
    print("Step 2: Generating test scenarios...")
    feature_specs = [
        FeatureSpec(name='credit_score', type='continuous', range=(300, 850), distribution='normal', mean=680, std=80),
        FeatureSpec(name='annual_income', type='continuous', range=(20000, 200000), distribution='normal', mean=65000, std=30000),
        FeatureSpec(name='age', type='discrete', range=(18, 80)),
        FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 0.8), distribution='normal', mean=0.3, std=0.15)
    ]
    
    generator = ScenarioGenerator(feature_specs, random_seed=42)
    scenarios = generator.generate_monte_carlo(1000)
    print(f"✓ Generated {len(scenarios)} scenarios using Monte Carlo simulation")
    print()
    
    # Step 3: Execute Decisions
    print("Step 3: Executing decisions...")
    executor = DecisionExecutor(engine)
    results = executor.execute_batch(scenarios, store_audit_trail=False)
    
    decision_dist = executor.get_decision_distribution()
    print("✓ Execution complete")
    print(f"  Decision distribution:")
    for decision, count in decision_dist.items():
        print(f"    - {decision}: {count} ({count/len(scenarios)*100:.1f}%)")
    print()
    
    # Step 4: Detect Failures
    print("Step 4: Detecting failures and instabilities...")
    detector = FailureDetector()
    
    # Detect anomalies
    results_with_anomalies = detector.detect_anomalies(results, contamination=0.1)
    
    # Discover failure clusters
    results_with_clusters = detector.discover_failure_clusters(results, eps=0.5, min_samples=5)
    
    # Test instability
    print("  Testing decision instability on sample scenarios...")
    sample_scenarios = scenarios[:30]
    instabilities = detector.detect_instability(executor, sample_scenarios, n_perturbations=10)
    
    summary = detector.get_detection_summary()
    print(f"✓ Detection complete")
    print(f"  - Anomalies detected: {summary.get('total_anomalies', 0)}")
    print(f"  - Failure clusters: {summary.get('total_clusters', 0)}")
    print(f"  - Unstable scenarios: {summary.get('total_unstable_scenarios', 0)}")
    if summary.get('total_unstable_scenarios', 0) > 0:
        print(f"  - Avg instability score: {summary.get('avg_instability_score', 0):.3f}")
    print()
    
    # Step 5: Score Risks
    print("Step 5: Calculating risk scores...")
    scorer = RiskScorer()
    
    # Score instability
    scorer.score_instability(instabilities)
    
    # Find decision boundaries
    boundaries = executor.find_decision_boundaries('credit_score')
    scorer.score_conflict_density(results, boundaries)
    
    # Score coverage and concentration
    scorer.score_coverage_gaps(results)
    scorer.score_decision_concentration(results)
    scorer.score_confidence_variance(results)
    
    # Calculate composite risk
    composite = scorer.calculate_composite_risk_score()
    print(f"✓ Risk scoring complete")
    print(f"  - Overall severity: {composite['overall_severity'].upper()}")
    print(f"  - Composite risk score: {composite['composite_risk_score']:.3f} / 1.00")
    print()
    
    # Generate risk report
    print("Step 6: Generating risk report...")
    print()
    report = scorer.generate_risk_report()
    print(report)
    print()
    
    # Step 7: Generate Explanations
    if instabilities:
        print("Step 7: Generating explanations for instabilities...")
        explainer = ExplainabilityEngine(engine, executor)
        
        # Explain first instability
        first_instability = instabilities[0]
        explanation = explainer.explain_instability(first_instability)
        
        print(f"✓ Example explanation:")
        print(f"  {explanation['summary']}")
        print()
        
        if explanation['suggestions']:
            print(f"  Suggestions:")
            for sug in explanation['suggestions'][:2]:
                print(f"    - [{sug['priority'].upper()}] {sug['description']}")
        print()
    
    # Step 8: What-If Policy Repair
    if composite['composite_risk_score'] > 0.3:
        print("Step 8: Testing policy repair modifications...")
        repair_engine = PolicyRepairEngine(engine)
        
        # Get automatic suggestions
        suggestions = repair_engine.suggest_modifications(
            detector.detection_results,
            scorer.risk_scores
        )
        
        if suggestions:
            print(f"✓ Generated {len(suggestions)} modification suggestions")
            print(f"\n  Testing first suggestion...")
            
            # Test first suggestion
            first_suggestion = suggestions[0]
            print(f"  - {first_suggestion.description}")
            
            # Note: Simulation needs scenarios and executor, skipping for brevity
            print(f"  - Modification type: {first_suggestion.modification_type.value}")
        
        print()
    else:
        print("Step 8: Policy Repair")
        print("✓ Risk score is acceptably low - no modifications needed")
        print()
    
    # Step 9: Export Results
    print("Step 9: Exporting results...")
    output_path = Path(__file__).parent.parent / "outputs"
    output_path.mkdir(exist_ok=True)
    
    executor.export_results(str(output_path / "execution_results.csv"))
    scorer.export_risk_scores(str(output_path / "risk_scores.json"))
    
    print(f"✓ Results exported to {output_path}/")
    print()
    
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print()
    print("Key Findings:")
    print(f"  • {len(scenarios)} scenarios tested")
    print(f"  • {summary.get('total_anomalies', 0)} anomalous patterns detected")
    print(f"  • {len(boundaries)} decision boundaries found")
    print(f"  • Overall risk level: {composite['overall_severity'].upper()}")
    print()
    print("Next Steps:")
    print("  1. Review high-risk scenarios in outputs/execution_results.csv")
    print("  2. Examine risk breakdown in outputs/risk_scores.json")
    print("  3. Consider rule modifications based on suggestions")
    print("  4. Run Streamlit UI for interactive analysis: streamlit run src/ui/app.py")
    print()


if __name__ == "__main__":
    main()
