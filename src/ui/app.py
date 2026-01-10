"""
Policy Intelligence Engine - Streamlit UI

Enterprise-grade interface for stress-testing decision rules and discovering
hidden failures, conflicts, and systemic risks.
"""

import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src to path - handle both when run from root and from src/ui
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent
src_dir = root_dir / 'src'

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from policy_engine import RuleEngine
from scenario_generator import ScenarioGenerator, FeatureSpec, ScenarioType
from decision_executor import DecisionExecutor
from failure_detector import FailureDetector
from risk_scoring import RiskScorer
from explainability import ExplainabilityEngine


# Page configuration
st.set_page_config(
    page_title="Policy Intelligence Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enterprise styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .risk-critical {
        color: #dc2626;
        font-weight: 600;
    }
    .risk-high {
        color: #ea580c;
        font-weight: 600;
    }
    .risk-medium {
        color: #f59e0b;
        font-weight: 600;
    }
    .risk-low {
        color: #10b981;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'rule_engine' not in st.session_state:
        st.session_state.rule_engine = None
    if 'scenarios' not in st.session_state:
        st.session_state.scenarios = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'failure_detector' not in st.session_state:
        st.session_state.failure_detector = None
    if 'risk_scorer' not in st.session_state:
        st.session_state.risk_scorer = None


def render_header():
    """Render page header."""
    st.markdown('<div class="main-header">🔍 Policy Intelligence Engine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Discover hidden failures, conflicts, and systemic risk in decision rules</div>',
        unsafe_allow_html=True
    )


def section_define_system():
    """Section 1: Define Decision System."""
    st.header("1️⃣ Define Decision System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Load Rule Configuration")
        
        # Option to load example or upload
        load_option = st.radio(
            "Choose option:",
            ["Load Example (Credit Risk)", "Upload Custom Rules"],
            horizontal=True
        )
        
        rules_path = None
        
        if load_option == "Load Example (Credit Risk)":
            example_path = root_dir / "examples" / "credit_risk_rules.json"
            if example_path.exists():
                rules_path = str(example_path)
                st.success("✅ Example rules loaded")
            else:
                st.error("Example file not found")
        else:
            uploaded_file = st.file_uploader("Upload rules (JSON)", type=['json'])
            if uploaded_file:
                # Save temporarily
                temp_path = Path("/tmp/uploaded_rules.json")
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                rules_path = str(temp_path)
                st.success("✅ Custom rules uploaded")
        
        # Load rules
        if rules_path and st.button("Load Rules", type="primary"):
            try:
                engine = RuleEngine(rules_path)
                st.session_state.rule_engine = engine
                
                summary = engine.get_rule_summary()
                st.success(f"✅ Rules loaded successfully: {summary['rule_set_name']}")
                
            except Exception as e:
                st.error(f"Error loading rules: {str(e)}")
    
    with col2:
        if st.session_state.rule_engine:
            summary = st.session_state.rule_engine.get_rule_summary()
            
            st.metric("Rule Set", summary['rule_set_name'])
            st.metric("Total Rules", summary['total_rules'])
            st.metric("Unique Features", summary['unique_features'])
            st.metric("Decision Types", len(summary['decision_outcomes']))
            
            with st.expander("View Rules"):
                for rule in st.session_state.rule_engine.rules['rules']:
                    st.markdown(f"**{rule['rule_id']}**: {rule.get('name', 'Unnamed')}")
                    st.caption(f"Priority: {rule['priority']} → Decision: {rule['decision']['outcome']}")


def section_stress_test():
    """Section 2: Stress-Test Scenarios."""
    st.header("2️⃣ Stress-Test Scenarios")
    
    if not st.session_state.rule_engine:
        st.warning("⚠️ Please load rules first (Section 1)")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Configure Scenario Generation")
        
        # Feature specifications (example for credit risk)
        st.markdown("**Define Feature Space:**")
        
        num_features = st.number_input("Number of features", min_value=1, max_value=10, value=4)
        
        feature_specs = []
        for i in range(num_features):
            with st.expander(f"Feature {i+1}"):
                fname = st.text_input(f"Name", value=f"feature_{i}", key=f"fname_{i}")
                ftype = st.selectbox(f"Type", ["continuous", "discrete", "categorical"], key=f"ftype_{i}")
                
                if ftype in ["continuous", "discrete"]:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        fmin = st.number_input(f"Min", value=0.0, key=f"fmin_{i}")
                    with col_b:
                        fmax = st.number_input(f"Max", value=100.0, key=f"fmax_{i}")
                    
                    feature_specs.append(
                        FeatureSpec(name=fname, type=ftype, range=(fmin, fmax))
                    )
                else:
                    values_str = st.text_input(f"Values (comma-separated)", value="A,B,C", key=f"fvals_{i}")
                    values = [v.strip() for v in values_str.split(',')]
                    feature_specs.append(
                        FeatureSpec(name=fname, type=ftype, values=values)
                    )
        
        # Scenario generation options
        st.markdown("**Generation Strategy:**")
        
        generation_type = st.selectbox(
            "Scenario Type",
            ["Monte Carlo (Mixed)", "Normal Cases", "Boundary Cases", "Adversarial Cases"]
        )
        
        n_scenarios = st.slider("Number of scenarios", 100, 5000, 1000)
        
        if st.button("Generate Scenarios", type="primary"):
            generator = ScenarioGenerator(feature_specs, random_seed=42)
            
            if generation_type == "Monte Carlo (Mixed)":
                scenarios = generator.generate_monte_carlo(n_scenarios)
            elif generation_type == "Normal Cases":
                scenarios = generator.generate(n_scenarios, ScenarioType.NORMAL)
            elif generation_type == "Boundary Cases":
                scenarios = generator.generate(n_scenarios, ScenarioType.BOUNDARY)
            else:
                scenarios = generator.generate(n_scenarios, ScenarioType.ADVERSARIAL)
            
            st.session_state.scenarios = scenarios
            st.success(f"✅ Generated {len(scenarios)} scenarios")
    
    with col2:
        if st.session_state.scenarios:
            st.metric("Scenarios Generated", len(st.session_state.scenarios))
            
            # Preview scenarios
            with st.expander("Preview Scenarios"):
                df_preview = pd.DataFrame(st.session_state.scenarios[:10])
                st.dataframe(df_preview)


def section_discover_failures():
    """Section 3: Discover Failure Modes."""
    st.header("3️⃣ Discover Failure Modes")
    
    if not st.session_state.rule_engine or not st.session_state.scenarios:
        st.warning("⚠️ Please load rules and generate scenarios first")
        return
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        if st.button("Run Analysis", type="primary", key="run_analysis"):
            with st.spinner("Executing scenarios..."):
                # Execute scenarios
                executor = DecisionExecutor(st.session_state.rule_engine)
                results_df = executor.execute_batch(st.session_state.scenarios)
                st.session_state.results = results_df
                st.session_state.executor = executor
            
            with st.spinner("Detecting anomalies..."):
                # Detect failures
                detector = FailureDetector()
                results_with_anomalies = detector.detect_anomalies(results_df, contamination=0.1)
                results_with_clusters = detector.discover_failure_clusters(results_df)
                
                st.session_state.failure_detector = detector
                st.session_state.results = results_with_anomalies
            
            with st.spinner("Analyzing instability..."):
                # Test instability on sample
                sample_scenarios = st.session_state.scenarios[:50]  # Test 50 scenarios
                instabilities = detector.detect_instability(executor, sample_scenarios, n_perturbations=10)
            
            st.success("✅ Analysis complete!")
    
    with col2:
        if st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            
            st.metric("Anomalies Found", summary.get('total_anomalies', 0))
            st.metric("Failure Clusters", summary.get('total_clusters', 0))
            st.metric("Unstable Scenarios", summary.get('total_unstable_scenarios', 0))
    
    # Display detailed results
    if st.session_state.results is not None:
        st.subheader("Detection Results")
        
        tab1, tab2, tab3 = st.tabs(["Anomalies", "Clusters", "Decision Distribution"])
        
        with tab1:
            if 'is_anomaly' in st.session_state.results.columns:
                anomalies = st.session_state.results[st.session_state.results['is_anomaly']]
                st.write(f"**{len(anomalies)} anomalous scenarios detected**")
                
                if len(anomalies) > 0:
                    # Show top anomalies by score
                    top_anomalies = anomalies.nsmallest(10, 'anomaly_score')
                    st.dataframe(top_anomalies[['scenario_id', 'decision', 'anomaly_score', 'confidence']])
        
        with tab2:
            if st.session_state.failure_detector and 'clusters' in st.session_state.failure_detector.detection_results:
                clusters_df = st.session_state.failure_detector.detection_results['clusters']
                st.dataframe(clusters_df)
        
        with tab3:
            decision_dist = st.session_state.results['decision'].value_counts()
            
            fig = px.pie(
                values=decision_dist.values,
                names=decision_dist.index,
                title="Decision Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)


def section_risk_dashboard():
    """Section 4: Risk Dashboard."""
    st.header("4️⃣ Risk Dashboard")
    
    if st.session_state.results is None:
        st.warning("⚠️ Please run analysis first (Section 3)")
        return
    
    # Calculate risk scores
    if st.button("Calculate Risk Scores", type="primary"):
        scorer = RiskScorer()
        
        # Score different risk factors
        if st.session_state.failure_detector:
            instabilities = st.session_state.failure_detector.detection_results.get('instabilities', [])
            scorer.score_instability(instabilities)
        
        if st.session_state.executor:
            # Find boundaries
            feature_cols = [col for col in st.session_state.results.columns if col.startswith('feature_')]
            boundaries = []
            for col in feature_cols[:3]:  # Analyze first 3 features
                feature_name = col.replace('feature_', '')
                bounds = st.session_state.executor.find_decision_boundaries(feature_name)
                boundaries.extend(bounds)
            
            scorer.score_conflict_density(st.session_state.results, boundaries)
        
        scorer.score_coverage_gaps(st.session_state.results)
        scorer.score_decision_concentration(st.session_state.results)
        scorer.score_confidence_variance(st.session_state.results)
        
        st.session_state.risk_scorer = scorer
    
    # Display risk dashboard
    if st.session_state.risk_scorer:
        composite = st.session_state.risk_scorer.calculate_composite_risk_score()
        
        # Overall risk score
        st.subheader("Overall Risk Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity = composite['overall_severity']
            severity_class = f"risk-{severity}"
            st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="{severity_class}" style="font-size: 2rem;">{severity.upper()}</div>', unsafe_allow_html=True)
            st.markdown(f'<div>Overall Severity</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            score = composite['composite_risk_score']
            st.metric("Composite Risk Score", f"{score:.2f}", help="Scale: 0.0 (low) to 1.0 (critical)")
        
        with col3:
            st.metric("Risk Factors Analyzed", len(composite.get('risk_breakdown', {})))
        
        # Risk breakdown
        st.subheader("Risk Factor Breakdown")
        
        breakdown = composite.get('risk_breakdown', {})
        if breakdown:
            df_breakdown = pd.DataFrame([
                {
                    'Risk Factor': k.replace('_', ' ').title(),
                    'Severity': v['severity'],
                    'Contribution': v['contribution']
                }
                for k, v in breakdown.items()
            ])
            
            fig = px.bar(
                df_breakdown,
                x='Risk Factor',
                y='Contribution',
                color='Severity',
                title="Risk Contribution by Factor",
                color_discrete_map={
                    'low': '#10b981',
                    'medium': '#f59e0b',
                    'high': '#ea580c',
                    'critical': '#dc2626'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed scores
        with st.expander("View Detailed Risk Scores"):
            st.json(composite['detailed_scores'])


def section_what_if():
    """Section 5: What-If Rule Repair."""
    st.header("5️⃣ What-If Rule Repair")
    
    if not st.session_state.rule_engine:
        st.warning("⚠️ Please load rules first")
        return
    
    st.subheader("Simulate Rule Modifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Select Rule to Modify:**")
        
        if st.session_state.rule_engine.rules:
            rule_ids = [r['rule_id'] for r in st.session_state.rule_engine.rules['rules']]
            selected_rule_id = st.selectbox("Rule ID", rule_ids)
            
            # Show current rule
            selected_rule = next(
                r for r in st.session_state.rule_engine.rules['rules']
                if r['rule_id'] == selected_rule_id
            )
            
            st.json(selected_rule)
            
            st.markdown("**Suggested Modifications:**")
            st.info("""
            Based on detected failures:
            1. Add buffer zones around decision boundaries
            2. Consolidate overlapping rules
            3. Adjust threshold values for stability
            4. Add intermediate decision categories
            """)
    
    with col2:
        st.markdown("**Impact Simulation:**")
        
        if st.button("Simulate Impact"):
            st.info("This feature allows you to modify rules and see the projected impact on risk scores before deploying changes.")
            st.warning("⚠️ Feature in development - use explainability insights to guide manual modifications")


def main():
    """Main application."""
    init_session_state()
    render_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        section = st.radio(
            "Go to:",
            [
                "1️⃣ Define System",
                "2️⃣ Stress-Test",
                "3️⃣ Discover Failures",
                "4️⃣ Risk Dashboard",
                "5️⃣ What-If Analysis"
            ]
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        **Policy Intelligence Engine**
        
        Stress-tests human decision rules to discover:
        - Hidden failures
        - Rule conflicts
        - Decision instability
        - Systemic risks
        """)
        
        st.markdown("---")
        st.caption("Built for enterprise policy analysis")
    
    # Render selected section
    if "Define System" in section:
        section_define_system()
    elif "Stress-Test" in section:
        section_stress_test()
    elif "Discover Failures" in section:
        section_discover_failures()
    elif "Risk Dashboard" in section:
        section_risk_dashboard()
    elif "What-If" in section:
        section_what_if()


if __name__ == "__main__":
    main()
