# Policy Intelligence Engine

> **An AI system that stress-tests human decision rules to discover hidden failures, conflicts, and systemic risk before they impact the real world.**

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

---

## 🎯 Problem Statement

Human-defined decision rules power critical systems across domains—from credit approvals to healthcare triage, from hiring decisions to resource allocation. These rules are deterministic, explainable, and seemingly safe. Yet they harbor hidden dangers:

- **Rule Conflicts**: Overlapping conditions that produce inconsistent decisions
- **Decision Instability**: Small input changes causing dramatic outcome shifts  
- **Coverage Gaps**: Unhandled edge cases that fall through the cracks
- **Systemic Risk**: Failure modes that only emerge under stress or at scale

Traditional testing validates expected behavior. **Policy Intelligence Engine** discovers what you didn't anticipate.

---

## 🏗️ System Architecture

### Core Design Principles

1. **Discovery over Prediction**: We don't optimize for accuracy—we find what breaks
2. **Determinism + Intelligence**: Rule engine is deterministic; ML finds the edge cases
3. **Complete Explainability**: Every detected issue comes with root cause and fix suggestions
4. **Domain Agnostic**: Works for any rule-based decision system
5. **Stress-First**: Tests under adversarial, boundary, and rare scenarios

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    POLICY INTELLIGENCE ENGINE                    │
└─────────────────────────────────────────────────────────────────┘

Input Layer
├── Rule Engine (Deterministic)
│   ├── JSON/YAML rule definitions
│   ├── Condition evaluation
│   └── Decision execution with audit trails

Stress Testing Layer  
├── Scenario Generator
│   ├── Monte Carlo simulation
│   ├── Boundary case generation
│   ├── Adversarial perturbations
│   └── Grid search for systematic coverage

Execution Layer
├── Decision Executor
│   ├── Batch rule execution
│   ├── Decision tracking
│   └── Pattern analysis

Intelligence Layer (ML Core)
├── Failure & Instability Detector
│   ├── Anomaly Detection (Isolation Forest, LOF)
│   ├── Clustering (DBSCAN for failure modes)
│   ├── Instability Testing (perturbation analysis)
│   └── Edge Case Discovery

Assessment Layer
├── Risk & Impact Scoring
│   ├── Instability scores
│   ├── Conflict density metrics
│   ├── Coverage gap analysis
│   ├── Decision concentration
│   └── Composite risk assessment

Insight Layer
├── Explainability Engine
│   ├── Root cause analysis
│   ├── Rule conflict detection
│   ├── What-if analysis
│   └── Actionable recommendations

Interface Layer
└── Streamlit UI (Enterprise-grade)
    ├── Rule definition & loading
    ├── Scenario generation
    ├── Live analysis dashboard
    ├── Risk visualization
    └── What-if rule repair
```

---

## 🚀 Quick Start

### Prerequisites

**Supported Python Versions:** 3.9, 3.10, 3.11

This system requires Python 3.9 or higher due to modern type hinting syntax and dependency compatibility requirements.

### Installation

```bash
# Clone the repository
git clone https://github.com/ravigohel142996/policy-intelligence-engine.git
cd policy-intelligence-engine

# Install dependencies
pip install -r requirements.txt
```

### Running the System

**Option 1: Streamlit UI (Recommended)**

```bash
streamlit run src/ui/app.py
```

**Option 2: Python API**

```python
from src.policy_engine import RuleEngine
from src.scenario_generator import ScenarioGenerator, FeatureSpec
from src.decision_executor import DecisionExecutor
from src.failure_detector import FailureDetector
from src.risk_scoring import RiskScorer

# Load rules
engine = RuleEngine('examples/credit_risk_rules.json')

# Generate test scenarios
feature_specs = [
    FeatureSpec(name='credit_score', type='continuous', range=(300, 850)),
    FeatureSpec(name='annual_income', type='continuous', range=(20000, 200000)),
    FeatureSpec(name='age', type='discrete', range=(18, 80)),
    FeatureSpec(name='debt_to_income', type='continuous', range=(0.0, 1.0))
]
generator = ScenarioGenerator(feature_specs, random_seed=42)
scenarios = generator.generate_monte_carlo(1000)

# Execute and analyze
executor = DecisionExecutor(engine)
results = executor.execute_batch(scenarios)

# Detect failures
detector = FailureDetector()
anomalies = detector.detect_anomalies(results, contamination=0.1)
instabilities = detector.detect_instability(executor, scenarios[:50])

# Score risk
scorer = RiskScorer()
scorer.score_instability(instabilities)
risk_report = scorer.calculate_composite_risk_score()
print(scorer.generate_risk_report())
```

---

## 📋 Rule Schema

Rules are defined in JSON/YAML format following this schema:

```json
{
  "rule_set_name": "example_system",
  "version": "1.0.0",
  "rules": [
    {
      "rule_id": "R001",
      "name": "High Risk Case",
      "priority": 1,
      "conditions": [
        {
          "feature": "risk_score",
          "operator": ">",
          "value": 0.8,
          "logical": "AND"
        }
      ],
      "decision": {
        "outcome": "reject",
        "confidence": 0.95,
        "reasoning": "Risk score exceeds threshold"
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

**Supported Operators**: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not_in`, `between`

---

## 🔬 Evaluation Philosophy

### Why Not Accuracy?

Traditional ML systems optimize for prediction accuracy. This system is fundamentally different:

| Traditional ML | Policy Intelligence |
|---------------|---------------------|
| Maximize accuracy | Discover failures |
| Test on labeled data | Stress-test with adversarial cases |
| Predict outcomes | Identify instability |
| Black box OK | Full explainability required |
| Optimize F1/AUC | Minimize systemic risk |

### Our Metrics

1. **Instability Score**: Measures decision sensitivity to input perturbations
2. **Conflict Density**: Quantifies rule overlap and boundary sharpness  
3. **Coverage Gap Rate**: Identifies unhandled scenario space
4. **Anomaly Detection**: Flags unusual scenarios for review
5. **Composite Risk Score**: Weighted combination of all risk factors

These metrics answer: *"What could go wrong at scale?"* not *"How often are we right?"*

---

## 🎓 Design Decisions

### Why Deterministic Rules + ML?

- **Rules**: Provide transparency, auditability, and domain expert control
- **ML**: Discovers patterns humans miss, especially in high-dimensional edge cases
- **Separation**: Rules make decisions; ML finds where rules break

### Why Simulation over Real Data?

1. **Privacy**: No sensitive data required
2. **Completeness**: Can generate rare scenarios that don't exist in historical data
3. **Control**: Systematic exploration of entire scenario space
4. **Generalization**: Not biased by past data distribution

### Why Focus on Instability?

Decision instability is a leading indicator of:
- Conflicting rules
- Insufficient rule coverage
- Overfitted thresholds
- Systemic fragility

A robust system should have smooth decision boundaries, not cliff edges.

---

## 📊 Use Cases

### Financial Services
- Credit risk assessment validation
- Fraud detection rule testing
- Loan approval policy analysis

### Healthcare
- Triage protocol stress-testing
- Treatment pathway validation
- Resource allocation rule review

### Human Resources
- Hiring policy fairness analysis
- Promotion criteria validation
- Compensation rule consistency

### Governance & Compliance
- Regulatory rule implementation
- Policy conflict detection
- Automated decision auditing

### Operations
- Resource allocation rules
- Priority scheduling validation
- Escalation policy testing

---

## 🔧 Development Setup

### Project Structure

```
policy-intelligence-engine/
├── src/
│   ├── policy_engine/       # Rule engine (deterministic)
│   ├── scenario_generator/  # Scenario generation
│   ├── decision_executor/   # Batch execution
│   ├── failure_detector/    # ML-based detection
│   ├── risk_scoring/        # Risk metrics
│   ├── explainability/      # Explanation generation
│   └── ui/                  # Streamlit interface
├── config/
│   └── rule_schema.json     # JSON schema for rules
├── examples/
│   └── credit_risk_rules.json
├── tests/                   # Unit tests
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v --cov=src
```

---

## 🚦 Scalability Considerations

### Current Limitations

- **In-memory processing**: Limited by available RAM
- **Single-threaded**: No parallel execution yet
- **Local compute**: Designed for Colab/Jupyter environments

### Scaling Strategies

1. **Batch Processing**: Process scenarios in chunks
2. **Sampling**: Use representative samples for large rule sets
3. **Incremental Analysis**: Run periodic checks rather than full analysis
4. **Distributed**: Future: Add Dask/Ray for parallel processing

### Production Deployment

For production use:
1. Wrap in containerized service (Docker)
2. Add API layer (FastAPI)
3. Implement result caching
4. Add monitoring and logging
5. Schedule periodic policy audits

---

## ⚖️ Ethical Considerations

### Responsible Use

This tool is designed to **improve** decision systems, not replace human judgment:

✅ **Appropriate Uses**:
- Auditing existing decision rules
- Finding edge cases before deployment
- Validating fairness and consistency
- Stress-testing policy changes

❌ **Inappropriate Uses**:
- Circumventing regulatory oversight
- Optimizing discriminatory rules
- Replacing human review processes
- Making automated decisions in high-stakes domains

### Fairness & Bias

While this system can detect instability and conflicts, it cannot guarantee fairness. Always:
- Test rules across protected groups
- Review ML-detected patterns for bias
- Combine with domain expertise
- Maintain human oversight

### Transparency

All components are designed for explainability:
- Rules are human-readable
- Every decision has an audit trail
- ML detections come with explanations
- Risk scores are decomposable

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Additional ML detection methods (One-Class SVM, Autoencoders)
- [ ] Real-time scenario generation
- [ ] Rule recommendation engine
- [ ] Fairness-specific metrics
- [ ] Integration with popular rule engines (Drools, etc.)
- [ ] Performance optimizations
- [ ] Additional UI visualizations

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- **scikit-learn**: ML algorithms
- **Streamlit**: UI framework
- **Plotly**: Visualizations
- **pandas/numpy**: Data processing

---

## 📞 Contact

For questions, issues, or collaboration:
- GitHub Issues: [Report a bug](https://github.com/ravigohel142996/policy-intelligence-engine/issues)
- Discussions: [Join the conversation](https://github.com/ravigohel142996/policy-intelligence-engine/discussions)

---

**Remember**: The goal isn't to find all failures—it's to find the failures that matter before they do.
