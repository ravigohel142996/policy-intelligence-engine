# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/ravigohel142996/policy-intelligence-engine.git
cd policy-intelligence-engine

# Install dependencies
pip install -r requirements.txt
```

## Running the System

### Option 1: Interactive UI (Recommended)

Launch the Streamlit interface:

```bash
streamlit run src/ui/app.py
```

Then open your browser to `http://localhost:8501`

Navigate through the 5 sections:
1. **Define System**: Load or upload rule configurations
2. **Stress-Test**: Generate scenarios using Monte Carlo, boundary, or adversarial strategies
3. **Discover Failures**: Run analysis to detect anomalies, clusters, and instabilities
4. **Risk Dashboard**: View comprehensive risk assessment with severity scores
5. **What-If Analysis**: Explore rule modifications and their impacts

### Option 2: Command Line Example

Run the example workflow:

```bash
python examples/example_workflow.py
```

This demonstrates a complete analysis pipeline:
- Loads credit risk rules
- Generates 1000 test scenarios
- Executes decisions
- Detects failures and instabilities
- Calculates risk scores
- Generates explanations
- Exports results to `outputs/`

### Option 3: Python API

```python
from src.policy_engine import RuleEngine
from src.scenario_generator import ScenarioGenerator, FeatureSpec
from src.decision_executor import DecisionExecutor
from src.failure_detector import FailureDetector
from src.risk_scoring import RiskScorer

# Load rules
engine = RuleEngine('examples/credit_risk_rules.json')

# Generate scenarios
specs = [
    FeatureSpec(name='credit_score', type='continuous', range=(300, 850)),
    FeatureSpec(name='annual_income', type='continuous', range=(20000, 200000)),
    FeatureSpec(name='age', type='discrete', range=(18, 80)),
    FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 1.0))
]
generator = ScenarioGenerator(specs, random_seed=42)
scenarios = generator.generate_monte_carlo(1000)

# Execute and analyze
executor = DecisionExecutor(engine)
results = executor.execute_batch(scenarios)

detector = FailureDetector()
anomalies = detector.detect_anomalies(results)
instabilities = detector.detect_instability(executor, scenarios[:50])

scorer = RiskScorer()
scorer.score_instability(instabilities)
risk_report = scorer.calculate_composite_risk_score()
print(scorer.generate_risk_report())
```

## Example Use Cases

### Credit Risk Assessment
```bash
# Uses examples/credit_risk_rules.json
python examples/example_workflow.py
```

### Healthcare Triage
```python
from src.policy_engine import RuleEngine

# Load healthcare rules
engine = RuleEngine('examples/healthcare_triage_rules.json')

# Define healthcare feature space
specs = [
    FeatureSpec(name='heart_rate', type='continuous', range=(40, 180)),
    FeatureSpec(name='blood_pressure_systolic', type='continuous', range=(70, 200)),
    FeatureSpec(name='pain_level', type='discrete', range=(0, 10)),
    FeatureSpec(name='consciousness_level', type='discrete', range=(3, 15)),
    # ... more features
]

# Continue with scenario generation and analysis
```

## Customizing Rules

Create your own rule file in JSON format:

```json
{
  "rule_set_name": "my_policy",
  "version": "1.0.0",
  "rules": [
    {
      "rule_id": "R001",
      "name": "High Risk",
      "priority": 1,
      "conditions": [
        {
          "feature": "risk_score",
          "operator": ">",
          "value": 0.8
        }
      ],
      "decision": {
        "outcome": "reject",
        "confidence": 0.95,
        "reasoning": "Risk exceeds threshold"
      },
      "stop_on_match": true
    }
  ],
  "default_decision": {
    "outcome": "review",
    "reasoning": "No rules matched"
  }
}
```

See `config/rule_schema.json` for the complete schema.

## Running Tests

```bash
python tests/test_components.py
```

## Outputs

Results are saved to `outputs/`:
- `execution_results.csv`: Detailed scenario execution results
- `risk_scores.json`: Risk assessment breakdown

## Next Steps

1. **Review the README**: Comprehensive documentation on architecture and design
2. **Explore Examples**: See `examples/` for different domain configurations
3. **Customize Rules**: Create rules for your specific domain
4. **Analyze Results**: Use the UI or API to stress-test your policies
5. **Iterate**: Modify rules based on discovered failures and retest

## Troubleshooting

**Issue**: Module not found errors
**Solution**: Ensure you've installed requirements: `pip install -r requirements.txt`

**Issue**: Streamlit UI not loading
**Solution**: Make sure you're in the project root and run: `streamlit run src/ui/app.py`

**Issue**: Path errors in tests
**Solution**: Run tests from project root: `python tests/test_components.py`

## Support

- **Documentation**: See README.md for comprehensive details
- **Issues**: Report bugs on GitHub Issues
- **Examples**: Check `examples/` directory for sample implementations

---

**Remember**: This system is designed to discover what could go wrong, not to optimize prediction accuracy. Focus on the insights it provides about rule conflicts, instabilities, and coverage gaps.
