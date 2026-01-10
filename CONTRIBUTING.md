# Contributing to Policy Intelligence Engine

Thank you for your interest in contributing to the Policy Intelligence Engine! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contribution Guidelines](#contribution-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Areas for Contribution](#areas-for-contribution)
7. [Testing](#testing)
8. [Code Style](#code-style)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or intimidation of any kind
- Trolling, insulting/derogatory comments, and personal or political attacks
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/policy-intelligence-engine.git
   cd policy-intelligence-engine
   ```
3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/ravigohel142996/policy-intelligence-engine.git
   ```

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv or conda)

### Setup Steps

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests to verify setup
python tests/test_components.py
```

---

## Contribution Guidelines

### Before You Start

1. **Check existing issues** to see if someone is already working on it
2. **Create an issue** if one doesn't exist for your proposed change
3. **Discuss major changes** in an issue before starting work
4. **Keep changes focused** - one feature or bug fix per PR

### Types of Contributions

We welcome:

- **Bug fixes** - Fix issues in existing code
- **New features** - Add functionality aligned with project goals
- **Documentation** - Improve or add documentation
- **Tests** - Add or improve test coverage
- **Examples** - Add new example rule sets for different domains
- **Performance improvements** - Optimize existing code
- **UI enhancements** - Improve the Streamlit interface

### Design Principles (Non-Negotiable)

When contributing, adhere to these core principles:

1. **Discovery over Prediction** - Focus on finding failures, not optimizing accuracy
2. **Explainability Required** - Every component must be interpretable
3. **Domain Agnostic** - Solutions should work across all domains
4. **Production Quality** - Write maintainable, well-documented code
5. **Minimize ML Complexity** - Use ML only where it adds unique value

---

## Pull Request Process

### 1. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, documented code
- Add tests for new functionality
- Update documentation as needed
- Follow the code style guidelines

### 3. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add: Brief description of what was added"
```

Commit message prefixes:
- `Add:` - New feature or file
- `Fix:` - Bug fix
- `Update:` - Modification to existing feature
- `Refactor:` - Code restructuring without functional changes
- `Docs:` - Documentation changes
- `Test:` - Test additions or modifications

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with:
- **Clear title** describing the change
- **Detailed description** of what and why
- **Link to related issue** if applicable
- **Screenshots** for UI changes
- **Test results** showing your changes work

### 5. Code Review

- Respond to review comments promptly
- Make requested changes in new commits
- Keep discussions professional and constructive

### 6. Merge

Once approved, a maintainer will merge your PR.

---

## Areas for Contribution

### High Priority

- [ ] **Additional ML Detection Methods**
  - One-Class SVM for anomaly detection
  - Autoencoder-based detection
  - Ensemble methods

- [ ] **Real-time Scenario Generation**
  - Streaming scenario generation
  - Adaptive sampling based on findings

- [ ] **Rule Recommendation Engine**
  - Suggest rule modifications automatically
  - Generate new rules from patterns

- [ ] **Fairness-Specific Metrics**
  - Demographic parity analysis
  - Equal opportunity metrics
  - Bias detection algorithms

### Medium Priority

- [ ] **Integration with Rule Engines**
  - Drools integration
  - DMN (Decision Model and Notation) support
  - Business rules engine adapters

- [ ] **Performance Optimizations**
  - Parallel processing support
  - Distributed computing (Dask/Ray)
  - Caching improvements

- [ ] **Additional Visualizations**
  - Interactive decision tree visualization
  - 3D feature space plots
  - Animated boundary transitions

- [ ] **API Layer**
  - REST API with FastAPI
  - GraphQL endpoint
  - WebSocket for real-time updates

### Domain-Specific Examples

Add new example rule sets for:
- [ ] Insurance underwriting
- [ ] Content moderation
- [ ] Supply chain allocation
- [ ] Academic admissions
- [ ] Fraud detection
- [ ] Customer segmentation

---

## Testing

### Running Tests

```bash
# Run all tests
python tests/test_components.py

# Run specific test
pytest tests/ -k test_rule_engine -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

- **Test file naming:** `test_*.py`
- **Test function naming:** `test_<functionality>()`
- **Use descriptive names** that explain what is being tested
- **Include edge cases** and failure scenarios
- **Mock external dependencies** when appropriate

Example:

```python
def test_rule_engine_executes_correctly():
    """Test that rule engine correctly executes a simple scenario."""
    engine = RuleEngine('examples/credit_risk_rules.json')
    scenario = {'credit_score': 750, 'annual_income': 80000}
    result = engine.execute(scenario)
    assert result['decision'] is not None
    assert 'audit_trail' in result
```

### Test Coverage Goals

- Core modules: 80%+ coverage
- New features: Must include tests
- Bug fixes: Add regression test

---

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length:** 100 characters (not 79)
- **Imports:** Group in order: standard library, third-party, local
- **Docstrings:** Google style for all public functions/classes
- **Type hints:** Use for function signatures

### Formatting Tools

```bash
# Auto-format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Documentation Style

- Use clear, concise language
- Include examples where helpful
- Explain the "why" not just the "what"
- Comment complex algorithms or business logic

Example:

```python
def calculate_instability_score(perturbations: List[Dict]) -> float:
    """
    Calculate instability score based on perturbation sensitivity.
    
    Instability indicates how often small input changes lead to different
    decisions - a key indicator of rule boundary issues.
    
    Args:
        perturbations: List of perturbation test results
        
    Returns:
        Float between 0 (stable) and 1 (highly unstable)
        
    Example:
        >>> perturbations = [{'changed': False}, {'changed': True}]
        >>> calculate_instability_score(perturbations)
        0.5
    """
    # Implementation
```

---

## Additional Resources

- **Architecture Documentation:** See [README.md](README.md)
- **Deployment Guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Example Workflows:** See [examples/example_workflow.py](examples/example_workflow.py)

---

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes for their contributions
- Special mentions for significant contributions

---

## Questions?

- **Technical questions:** Open a GitHub issue
- **General discussion:** Use GitHub Discussions
- **Security concerns:** Email maintainers directly (don't open public issues)

---

Thank you for contributing to making policy decision systems more robust and reliable!
