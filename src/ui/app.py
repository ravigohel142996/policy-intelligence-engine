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
from policy_repair import PolicyRepairEngine, RuleModification, ModificationType


# Page configuration
st.set_page_config(
    page_title="Policy Intelligence Engine",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Enterprise CSS - Calm, Minimal, Professional Command Center
st.markdown("""
<style>
    /* Global Styles - Clean Enterprise Aesthetic */
    .main {
        background-color: #ffffff;
        padding: 1rem 1.5rem;
    }
    
    .block-container {
        padding-top: 1rem;
        max-width: 100%;
    }
    
    /* Typography Hierarchy */
    .enterprise-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .enterprise-subtitle {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 400;
        margin-bottom: 1.5rem;
        line-height: 1.4;
        letter-spacing: 0.01em;
    }
    
    /* System Alert Band - Top Priority */
    .alert-band {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        border-left: 4px solid #64748b;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
    }
    
    .alert-band-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    
    .alert-band-critical {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #dc2626;
    }
    
    .alert-band-ok {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 4px solid #22c55e;
    }
    
    .alert-band-text {
        font-size: 0.95rem;
        color: #1e293b;
        font-weight: 500;
        line-height: 1.5;
        margin: 0;
    }
    
    /* Primary Signal - DOMINANT */
    .primary-signal-container {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 3rem 2rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05);
    }
    
    .primary-signal-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1rem;
    }
    
    .primary-signal-value {
        font-size: 4rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 1rem;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    
    .primary-signal-reason {
        font-size: 1rem;
        color: #475569;
        line-height: 1.6;
        max-width: 600px;
        margin: 0 auto;
    }
    
    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-top: 3rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #cbd5e1;
        letter-spacing: -0.01em;
    }
    
    .subsection-header {
        font-size: 1rem;
        font-weight: 600;
        color: #334155;
        margin-top: 2rem;
        margin-bottom: 1rem;
        letter-spacing: -0.005em;
    }
    
    /* Status Bar - Clean Minimal */
    .status-bar-container {
        background: #f8fafc;
        padding: 1.25rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Supporting Signals - With Reasoning */
    .supporting-signal-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.03);
        height: 100%;
    }
    
    .signal-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
        line-height: 1;
    }
    
    .signal-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }
    
    .signal-reason {
        font-size: 0.8rem;
        color: #64748b;
        line-height: 1.5;
        font-style: italic;
        border-top: 1px solid #f1f5f9;
        padding-top: 0.75rem;
        margin-top: 0.75rem;
    }
    
    /* Card Styles */
    .metric-card {
        background: white;
        padding: 1.25rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.03);
    }
    
    .info-card {
        background: #f8fafc;
        border-left: 3px solid #64748b;
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
    }
    
    .success-card {
        background: #f0fdf4;
        border-left: 3px solid #22c55e;
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
    }
    
    .warning-card {
        background: #fef3c7;
        border-left: 3px solid #f59e0b;
        padding: 1rem 1.25rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.02);
    }
    
    /* Key Insights List */
    .insights-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .insight-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.6;
    }
    
    .insight-item:last-child {
        border-bottom: none;
    }
    
    .insight-bullet {
        color: #64748b;
        margin-right: 0.5rem;
        font-weight: 600;
    }
    
    /* Next Action Box */
    .next-action-container {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px solid #cbd5e1;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 2rem 0 1rem 0;
    }
    
    .next-action-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }
    
    .next-action-text {
        font-size: 1rem;
        color: #1e293b;
        font-weight: 500;
        line-height: 1.6;
    }
    
    /* Risk Severity Colors - Professional */
    .risk-critical {
        color: #991b1b;
        font-weight: 600;
    }
    .risk-high {
        color: #c2410c;
        font-weight: 600;
    }
    .risk-medium {
        color: #b45309;
        font-weight: 600;
    }
    .risk-low {
        color: #047857;
        font-weight: 600;
    }
    
    /* Buttons - Subtle */
    .stButton>button {
        background-color: #1e293b;
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.15s;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    .stButton>button:hover {
        background-color: #334155;
        box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.1);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Spacing and Dividers */
    .spacer {
        margin: 1.5rem 0;
    }
    
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 2rem 0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Clean Dataframe Styles */
    .dataframe {
        font-size: 0.8rem;
        border: 1px solid #e2e8f0;
        border-radius: 0.375rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.375rem;
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.875rem;
    }
    
    /* Remove extra padding */
    .element-container {
        margin-bottom: 0.25rem;
    }
    
    /* Radio buttons - cleaner */
    .stRadio > label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #334155;
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
    if 'executor' not in st.session_state:
        st.session_state.executor = None
    if 'repair_engine' not in st.session_state:
        st.session_state.repair_engine = None
    if 'modification_results' not in st.session_state:
        st.session_state.modification_results = None
    if 'training_complete' not in st.session_state:
        st.session_state.training_complete = False
    if 'training_summary' not in st.session_state:
        st.session_state.training_summary = None
    if 'feature_specs' not in st.session_state:
        st.session_state.feature_specs = None


def render_header():
    """Render premium enterprise header."""
    st.markdown(
        '<div class="enterprise-title">Policy Intelligence Engine</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="enterprise-subtitle">'
        'Decision Intelligence Command Center'
        '</div>',
        unsafe_allow_html=True
    )


def render_status_bar():
    """Render top status bar with critical system metrics."""
    st.markdown('<div class="status-bar-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        rules_loaded = "Active" if st.session_state.rule_engine else "Not Loaded"
        st.metric(
            label="Rule System",
            value=rules_loaded
        )
    
    with col2:
        models_trained = "Trained" if st.session_state.training_complete else "Pending"
        st.metric(
            label="ML Models",
            value=models_trained
        )
    
    with col3:
        if st.session_state.results is not None and st.session_state.scenarios:
            coverage_pct = int((len(st.session_state.results) / len(st.session_state.scenarios)) * 100)
        else:
            coverage_pct = 0
        st.metric(
            label="Coverage",
            value=f"{coverage_pct}%"
        )
    
    with col4:
        # Determine overall risk level
        if st.session_state.risk_scorer:
            composite = st.session_state.risk_scorer.calculate_composite_risk_score()
            risk_level = composite['overall_severity'].upper()
        else:
            risk_level = "—"
        
        st.metric(
            label="Risk Level",
            value=risk_level
        )
    
    st.markdown('</div>', unsafe_allow_html=True)


def section_landing():
    """Landing / Overview section - Command Center view."""
    
    # 1. SYSTEM ALERT BAND (TOP) - Most important insight
    alert_class = "alert-band-ok"
    alert_message = "No critical conflicts detected. Monitoring instability zones."
    
    if st.session_state.risk_scorer:
        composite = st.session_state.risk_scorer.calculate_composite_risk_score()
        severity = composite['overall_severity']
        
        if severity == 'critical':
            alert_class = "alert-band-critical"
            alert_message = "Critical decision instability detected. Immediate review required."
        elif severity == 'high':
            alert_class = "alert-band-warning"
            alert_message = "Decision instability detected under boundary stress conditions."
        elif severity == 'medium':
            alert_class = "alert-band-warning"
            alert_message = "Moderate risk factors identified. Review recommended."
        elif st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            if summary.get('total_unstable_scenarios', 0) > 0:
                alert_class = "alert-band"
                alert_message = "Minor instability detected during stress testing. Continue monitoring."
    
    st.markdown(f'<div class="{alert_class}"><p class="alert-band-text">{alert_message}</p></div>', unsafe_allow_html=True)
    
    # 2. PRIMARY SYSTEM SIGNAL (DOMINANT)
    st.markdown('<div class="primary-signal-container">', unsafe_allow_html=True)
    st.markdown('<div class="primary-signal-title">Overall Decision Risk</div>', unsafe_allow_html=True)
    
    if st.session_state.risk_scorer:
        composite = st.session_state.risk_scorer.calculate_composite_risk_score()
        severity = composite['overall_severity'].upper()
        
        # Determine reason based on analysis
        reason = "Analysis complete. System evaluated across multiple risk dimensions."
        if st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            unstable = summary.get('total_unstable_scenarios', 0)
            anomalies = summary.get('total_anomalies', 0)
            
            if unstable > 10:
                reason = "Instability detected during boundary stress testing. Multiple scenarios show decision sensitivity."
            elif anomalies > 5:
                reason = "Anomalous patterns discovered via ML clustering on adversarial scenarios."
            else:
                reason = "System shows stable behavior. No significant failure modes detected."
    else:
        severity = "NOT ANALYZED"
        reason = "Complete analysis in Discover Failures section to assess system risk."
    
    st.markdown(f'<div class="primary-signal-value">{severity}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="primary-signal-reason">Reason: {reason}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 3. SUPPORTING SIGNALS (SECONDARY) - 4 metrics with reasoning
    st.markdown('<div class="subsection-header" style="margin-top: 2.5rem;">Supporting Signals</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        failure_count = 0
        failure_reason = "No analysis performed yet"
        
        if st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            failure_count = summary.get('total_anomalies', 0)
            
            if failure_count > 0:
                failure_reason = "Detected via anomaly clustering on adversarial scenarios"
            else:
                failure_reason = "No anomalous patterns discovered in stress tests"
        
        st.markdown('<div class="supporting-signal-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-label">Failure Modes Discovered</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-value">{failure_count}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-reason">{failure_reason}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        conflict_count = 0
        conflict_reason = "No boundary analysis performed"
        
        if st.session_state.results is not None and st.session_state.executor:
            # Estimate conflicts based on decision boundaries
            try:
                feature_cols = [col for col in st.session_state.results.columns if col.startswith('feature_')]
                if feature_cols:
                    boundaries = st.session_state.executor.find_decision_boundaries(
                        feature_cols[0].replace('feature_', '')
                    )
                    conflict_count = len(boundaries)
                    
                    if conflict_count > 0:
                        conflict_reason = "Overlapping decision boundaries identified"
                    else:
                        conflict_reason = "No direct rule conflicts detected"
            except:
                conflict_reason = "Boundary detection not available"
        
        st.markdown('<div class="supporting-signal-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-label">Rule Conflicts Detected</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-value">{conflict_count}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-reason">{conflict_reason}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        instability_index = 0.0
        instability_reason = "Perturbation tests not executed"
        
        if st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            total_tested = summary.get('total_scenarios_tested', 1)
            unstable = summary.get('total_unstable_scenarios', 0)
            instability_index = unstable / max(1, total_tested)
            
            if instability_index > 0.15:
                instability_reason = "High sensitivity to input perturbations detected"
            elif instability_index > 0.05:
                instability_reason = "Moderate instability under stress conditions"
            else:
                instability_reason = "Stable decisions across perturbation tests"
        
        st.markdown('<div class="supporting-signal-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-label">Instability Index</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-value">{instability_index:.1%}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-reason">{instability_reason}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        coverage_pct = 0
        coverage_reason = "Scenario generation required"
        
        if st.session_state.results is not None and st.session_state.scenarios:
            coverage_pct = int((len(st.session_state.results) / len(st.session_state.scenarios)) * 100)
            
            if coverage_pct >= 100:
                coverage_reason = "Complete scenario analysis executed"
            elif coverage_pct >= 50:
                coverage_reason = "Partial analysis completed"
            else:
                coverage_reason = "Initial analysis phase"
        
        st.markdown('<div class="supporting-signal-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-label">Analysis Coverage</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-value">{coverage_pct}%</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="signal-reason">{coverage_reason}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. KEY INSIGHTS SECTION
    st.markdown('<div class="subsection-header" style="margin-top: 2.5rem;">Key Insights</div>', unsafe_allow_html=True)
    
    insights = []
    
    if st.session_state.failure_detector:
        summary = st.session_state.failure_detector.get_detection_summary()
        
        # Generate intelligence-focused insights
        if summary.get('total_anomalies', 0) > 0:
            insights.append("Anomalous decision patterns emerge primarily in boundary regions")
        else:
            insights.append("No distinct failure clusters identified across scenario space")
        
        unstable = summary.get('total_unstable_scenarios', 0)
        if unstable > 10:
            insights.append("Most failures emerge near threshold boundaries under perturbation")
        elif unstable > 0:
            insights.append("Minor instability detected in edge case scenarios")
        else:
            insights.append("System demonstrates stable behavior across perturbation tests")
        
        if summary.get('total_clusters', 0) > 1:
            insights.append(f"Multiple distinct failure modes discovered requiring separate mitigation")
        
        if st.session_state.risk_scorer:
            composite = st.session_state.risk_scorer.calculate_composite_risk_score()
            if composite['overall_severity'] in ['medium', 'high', 'critical']:
                insights.append("Risk concentration detected in specific decision regions")
    else:
        insights = [
            "System analysis not yet performed",
            "Run stress tests to generate behavioral insights",
            "ML models require training data from scenario execution"
        ]
    
    st.markdown('<div class="insights-container">', unsafe_allow_html=True)
    for insight in insights:
        st.markdown(f'<div class="insight-item"><span class="insight-bullet">▸</span>{insight}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 5. NEXT ACTION GUIDANCE
    st.markdown('<div class="subsection-header" style="margin-top: 2.5rem;">Recommended Next Actions</div>', unsafe_allow_html=True)
    
    next_action = "Begin by defining your decision system in Define System section"
    
    if st.session_state.risk_scorer:
        composite = st.session_state.risk_scorer.calculate_composite_risk_score()
        severity = composite['overall_severity']
        
        if severity == 'critical':
            next_action = "Immediate action required: Review boundary conditions in high-risk policy rules"
        elif severity in ['high', 'medium']:
            next_action = "Review unstable regions in Risk Dashboard and test policy modifications"
        else:
            next_action = "System shows healthy risk profile. Consider expanding scenario coverage"
    elif st.session_state.failure_detector:
        next_action = "Proceed to Risk Dashboard to quantify and assess discovered failure modes"
    elif st.session_state.scenarios:
        next_action = "Execute analysis in Discover Failures section to identify systemic risks"
    elif st.session_state.rule_engine:
        next_action = "Generate comprehensive stress test scenarios in Stress Test section"
    
    st.markdown('<div class="next-action-container">', unsafe_allow_html=True)
    st.markdown('<div class="next-action-title">What to do next</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="next-action-text">{next_action}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def section_define_system():
    """Section 1: Define Decision System."""
    st.markdown('<div class="section-header">Define Decision System</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="subsection-header">Load Rule Configuration</div>', unsafe_allow_html=True)
        
        # Option to load example or upload
        load_option = st.radio(
            "Configuration Source",
            ["Example: Credit Risk Assessment", "Upload Custom Rules"],
            horizontal=True,
            label_visibility="visible"
        )
        
        rules_path = None
        
        if load_option == "Example: Credit Risk Assessment":
            example_path = root_dir / "examples" / "credit_risk_rules.json"
            if example_path.exists():
                rules_path = str(example_path)
                st.markdown('<div class="info-card">Example rules ready to load</div>', unsafe_allow_html=True)
            else:
                st.error("Example file not found")
        else:
            uploaded_file = st.file_uploader("Select JSON file", type=['json'], label_visibility="collapsed")
            if uploaded_file:
                # Save temporarily
                temp_path = Path("/tmp/uploaded_rules.json")
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                rules_path = str(temp_path)
                st.markdown('<div class="success-card">Custom rules uploaded successfully</div>', unsafe_allow_html=True)
        
        # Load rules
        if rules_path and st.button("Load Rules", type="primary"):
            try:
                engine = RuleEngine(rules_path)
                st.session_state.rule_engine = engine
                
                summary = engine.get_rule_summary()
                st.markdown(
                    f'<div class="success-card"><strong>System loaded:</strong> {summary["rule_set_name"]}</div>',
                    unsafe_allow_html=True
                )
                
            except Exception as e:
                st.error(f"Error loading rules: {str(e)}")
    
    with col2:
        if st.session_state.rule_engine:
            summary = st.session_state.rule_engine.get_rule_summary()
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Rule Set", summary['rule_set_name'])
            st.metric("Total Rules", summary['total_rules'])
            st.metric("Unique Features", summary['unique_features'])
            st.metric("Decision Outcomes", len(summary['decision_outcomes']))
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("View Rule Details"):
                for rule in st.session_state.rule_engine.rules['rules']:
                    st.markdown(f"**{rule['rule_id']}**: {rule.get('name', 'Unnamed')}")
                    st.caption(f"Priority {rule['priority']} → {rule['decision']['outcome']}")
                    st.markdown("---")


def section_stress_test():
    """Section 2: Generate Training Data & Stress-Test Scenarios."""
    st.markdown('<div class="section-header">Stress Test Generation</div>', unsafe_allow_html=True)
    
    if not st.session_state.rule_engine:
        st.markdown('<div class="warning-card">Please load rules first in the Define System section.</div>', unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="subsection-header">Define Feature Space</div>', unsafe_allow_html=True)
        
        num_features = st.number_input("Number of Features", min_value=1, max_value=10, value=4)
        
        feature_specs = []
        for i in range(num_features):
            with st.expander(f"Feature {i+1} Configuration", expanded=(i==0)):
                fname = st.text_input("Feature Name", value=f"feature_{i}", key=f"fname_{i}")
                ftype = st.selectbox("Type", ["continuous", "discrete", "categorical"], key=f"ftype_{i}")
                
                if ftype in ["continuous", "discrete"]:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        fmin = st.number_input("Minimum Value", value=0.0, key=f"fmin_{i}")
                    with col_b:
                        fmax = st.number_input("Maximum Value", value=100.0, key=f"fmax_{i}")
                    
                    feature_specs.append(
                        FeatureSpec(name=fname, type=ftype, range=(fmin, fmax))
                    )
                else:
                    values_str = st.text_input("Values (comma-separated)", value="A,B,C", key=f"fvals_{i}")
                    values = [v.strip() for v in values_str.split(',')]
                    feature_specs.append(
                        FeatureSpec(name=fname, type=ftype, values=values)
                    )
        
        st.session_state.feature_specs = feature_specs
        
        st.markdown('<div class="subsection-header">Generation Strategy</div>', unsafe_allow_html=True)
        
        generation_mode = st.radio(
            "Mode",
            ["Training Dataset (Recommended)", "Custom Scenarios"],
            horizontal=True
        )
        
        if generation_mode == "Training Dataset (Recommended)":
            n_scenarios = st.slider(
                "Dataset Size", 
                min_value=1000, 
                max_value=20000, 
                value=5000,
                step=1000
            )
            
            if st.button("Generate Training Dataset", type="primary"):
                with st.spinner("Generating comprehensive training dataset..."):
                    generator = ScenarioGenerator(feature_specs, random_seed=42)
                    scenarios = generator.generate_training_dataset(n_scenarios)
                    st.session_state.scenarios = scenarios
                    st.markdown(
                        f'<div class="success-card"><strong>Success:</strong> Generated {len(scenarios):,} training scenarios</div>',
                        unsafe_allow_html=True
                    )
        
        else:
            generation_type = st.selectbox(
                "Scenario Type",
                ["Monte Carlo (Mixed)", "Normal Cases", "Boundary Cases", "Adversarial Cases"]
            )
            
            n_scenarios = st.slider("Number of Scenarios", 100, 10000, 1000, step=100)
            
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
                st.markdown(
                    f'<div class="success-card"><strong>Success:</strong> Generated {len(scenarios):,} scenarios</div>',
                    unsafe_allow_html=True
                )
    
    with col2:
        if st.session_state.scenarios:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Scenarios Generated", f"{len(st.session_state.scenarios):,}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Preview scenarios
            with st.expander("Preview Sample Data"):
                df_preview = pd.DataFrame(st.session_state.scenarios[:10])
                st.dataframe(df_preview, use_container_width=True)


def section_discover_failures():
    """Section 3: Train Models & Discover Failure Modes."""
    st.markdown('<div class="section-header">Failure Discovery</div>', unsafe_allow_html=True)
    
    if not st.session_state.rule_engine or not st.session_state.scenarios:
        st.markdown('<div class="warning-card">Load rules and generate scenarios first.</div>', unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="subsection-header">Execute Analysis</div>', unsafe_allow_html=True)
        
        contamination = st.slider(
            "Expected Anomaly Rate",
            min_value=0.05,
            max_value=0.30,
            value=0.10,
            step=0.05
        )
        
        if st.button("Run Analysis & Training", type="primary", key="run_analysis"):
            
            # Step 1: Execute scenarios
            with st.spinner("Step 1/4: Executing scenarios..."):
                executor = DecisionExecutor(st.session_state.rule_engine)
                results_df = executor.execute_batch(st.session_state.scenarios)
                st.session_state.results = results_df
                st.session_state.executor = executor
                st.markdown('<div class="success-card">Scenarios executed</div>', unsafe_allow_html=True)
            
            # Step 2: Train ML models
            with st.spinner("Step 2/4: Training ML models..."):
                detector = FailureDetector()
                training_summary = detector.train(results_df, contamination=contamination)
                st.session_state.training_summary = training_summary
                st.session_state.training_complete = True
                st.markdown('<div class="success-card">Models trained successfully</div>', unsafe_allow_html=True)
            
            # Step 3: Detect anomalies
            with st.spinner("Step 3/4: Detecting anomalies..."):
                results_with_anomalies = detector.detect_anomalies(results_df, contamination=contamination)
                results_with_clusters = detector.discover_failure_clusters(results_df)
                
                st.session_state.failure_detector = detector
                st.session_state.results = results_with_anomalies
                st.markdown('<div class="success-card">Anomalies identified</div>', unsafe_allow_html=True)
            
            # Step 4: Test instability
            with st.spinner("Step 4/4: Testing instability..."):
                sample_size = min(50, len(st.session_state.scenarios))
                sample_scenarios = st.session_state.scenarios[:sample_size]
                instabilities = detector.detect_instability(executor, sample_scenarios, n_perturbations=10)
                st.markdown('<div class="success-card">Analysis complete</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="success-card"><strong>Complete:</strong> All models trained and failures identified</div>', unsafe_allow_html=True)
    
    with col2:
        if st.session_state.training_complete and st.session_state.training_summary:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("**Training Summary**")
            summary = st.session_state.training_summary
            st.write(f"Scenarios: {summary['training_scenarios']:,}")
            st.write(f"Features: {summary['n_features']}")
            st.write(f"Model: {summary['model_type']}")
            st.write(f"Clusters: {summary['n_clusters_discovered']}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.failure_detector:
            summary = st.session_state.failure_detector.get_detection_summary()
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Anomalies Found", summary.get('total_anomalies', 0))
            st.metric("Failure Clusters", summary.get('total_clusters', 0))
            st.metric("Unstable Scenarios", summary.get('total_unstable_scenarios', 0))
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Display detailed results
    if st.session_state.results is not None:
        st.markdown("---")
        st.markdown('<div class="subsection-header">Detection Results</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Anomalies", "Failure Clusters", "Decision Distribution"])
        
        with tab1:
            if 'is_anomaly' in st.session_state.results.columns:
                anomalies = st.session_state.results[st.session_state.results['is_anomaly']]
                st.markdown(f"**{len(anomalies)} anomalous scenarios detected**")
                
                if len(anomalies) > 0:
                    # Show top anomalies by score
                    top_anomalies = anomalies.nsmallest(10, 'anomaly_score')
                    st.dataframe(
                        top_anomalies[['scenario_id', 'decision', 'anomaly_score', 'confidence']],
                        use_container_width=True
                    )
        
        with tab2:
            if st.session_state.failure_detector and 'clusters' in st.session_state.failure_detector.detection_results:
                clusters_df = st.session_state.failure_detector.detection_results['clusters']
                if len(clusters_df) > 0:
                    st.dataframe(clusters_df, use_container_width=True)
                else:
                    st.info("No distinct failure clusters found")
        
        with tab3:
            decision_dist = st.session_state.results['decision'].value_counts()
            
            fig = px.pie(
                values=decision_dist.values,
                names=decision_dist.index,
                title="Decision Distribution",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_layout(
                showlegend=True,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)


def section_risk_dashboard():
    """Section 4: Risk Assessment & Quantification."""
    st.markdown('<div class="section-header">Risk Dashboard</div>', unsafe_allow_html=True)
    
    if st.session_state.results is None:
        st.markdown('<div class="warning-card">Complete analysis in Discover Failures section first.</div>', unsafe_allow_html=True)
        return
    
    # Calculate risk scores
    if st.button("Calculate Risk Scores", type="primary"):
        with st.spinner("Analyzing risk..."):
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
            st.markdown('<div class="success-card">Risk assessment complete</div>', unsafe_allow_html=True)
    
    # Display risk dashboard
    if st.session_state.risk_scorer:
        composite = st.session_state.risk_scorer.calculate_composite_risk_score()
        
        # Overall risk score
        st.markdown('<div class="subsection-header">Overall Assessment</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity = composite['overall_severity']
            severity_class = f"risk-{severity}"
            st.markdown('<div class="metric-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown(f'<div class="{severity_class}" style="font-size: 2.5rem; margin-bottom: 0.5rem;">{severity.upper()}</div>', unsafe_allow_html=True)
            st.markdown('<div style="color: #64748b;">Overall Severity</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            score = composite['composite_risk_score']
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Composite Risk Score", f"{score:.3f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Dimensions Analyzed", len(composite.get('risk_breakdown', {})))
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Risk breakdown
        st.markdown('<div class="subsection-header">Risk Factor Analysis</div>', unsafe_allow_html=True)
        
        breakdown = composite.get('risk_breakdown', {})
        if breakdown:
            df_breakdown = pd.DataFrame([
                {
                    'Risk Factor': k.replace('_', ' ').title(),
                    'Severity': v['severity'],
                    'Contribution': round(v['contribution'], 4)
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
            fig.update_layout(
                showlegend=True,
                xaxis_title="",
                yaxis_title="Risk Contribution",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed scores
        with st.expander("View Detailed Metrics"):
            st.json(composite['detailed_scores'])


def section_what_if():
    """Section 5: Policy Repair & What-If Analysis."""
    st.markdown('<div class="section-header">Policy Repair</div>', unsafe_allow_html=True)
    
    if not st.session_state.rule_engine:
        st.markdown('<div class="warning-card">Please load rules first in the Define System section.</div>', unsafe_allow_html=True)
        return
    
    # Initialize repair engine if not done
    if st.session_state.repair_engine is None and st.session_state.rule_engine is not None:
        st.session_state.repair_engine = PolicyRepairEngine(st.session_state.rule_engine)
    
    st.markdown('<div class="subsection-header">Modification Options</div>', unsafe_allow_html=True)
    
    # Show tabs for different workflows
    tab1, tab2, tab3 = st.tabs(["Manual Changes", "Suggested Improvements", "Impact Comparison"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Select Rule**")
            
            if st.session_state.rule_engine.rules:
                rule_ids = [r['rule_id'] for r in st.session_state.rule_engine.rules['rules']]
                selected_rule_id = st.selectbox("Rule ID", rule_ids, label_visibility="collapsed")
                
                # Show current rule
                selected_rule = next(
                    r for r in st.session_state.rule_engine.rules['rules']
                    if r['rule_id'] == selected_rule_id
                )
                
                with st.expander("View Current Rule Configuration"):
                    st.json(selected_rule)
                
                st.markdown("**Modification Type:**")
                mod_type = st.selectbox(
                    "Choose modification",
                    [
                        "Adjust Threshold",
                        "Change Priority",
                        "Add Buffer Zone",
                        "Modify Decision",
                        "Disable Rule"
                    ]
                )
                
                # Parameters based on modification type
                parameters = {}
                
                if mod_type == "Adjust Threshold":
                    st.markdown("**Threshold Adjustment:**")
                    condition_idx = st.number_input("Condition Index", min_value=0, 
                                                   max_value=len(selected_rule['conditions'])-1, value=0)
                    adjustment = st.slider("Adjustment Amount", -50.0, 50.0, 0.0, 0.5)
                    parameters = {
                        'condition_index': condition_idx,
                        'adjustment': adjustment
                    }
                    mod_type_enum = ModificationType.ADJUST_THRESHOLD
                    description = f"Adjust threshold in condition {condition_idx} by {adjustment}"
                
                elif mod_type == "Change Priority":
                    new_priority = st.number_input("New Priority", min_value=1, value=selected_rule['priority'])
                    parameters = {'new_priority': new_priority}
                    mod_type_enum = ModificationType.CHANGE_PRIORITY
                    description = f"Change priority from {selected_rule['priority']} to {new_priority}"
                
                elif mod_type == "Add Buffer Zone":
                    buffer_pct = st.slider("Buffer Zone (%)", 5, 30, 10) / 100
                    intermediate_decision = st.text_input("Intermediate Decision", "review")
                    parameters = {
                        'buffer_percent': buffer_pct,
                        'intermediate_decision': intermediate_decision
                    }
                    mod_type_enum = ModificationType.ADD_BUFFER_ZONE
                    description = f"Add {buffer_pct*100}% buffer zone with '{intermediate_decision}' decision"
                
                elif mod_type == "Modify Decision":
                    new_outcome = st.text_input("New Decision Outcome", selected_rule['decision']['outcome'])
                    new_reasoning = st.text_area("New Reasoning", selected_rule['decision']['reasoning'])
                    parameters = {
                        'decision_updates': {
                            'outcome': new_outcome,
                            'reasoning': new_reasoning
                        }
                    }
                    mod_type_enum = ModificationType.MODIFY_DECISION
                    description = f"Modify decision outcome to '{new_outcome}'"
                
                else:  # Disable Rule
                    parameters = {}
                    mod_type_enum = ModificationType.DISABLE_RULE
                    description = f"Disable rule {selected_rule_id}"
                
                # Simulate button
                if st.button("Simulate Impact", type="primary"):
                    if st.session_state.scenarios and st.session_state.executor and st.session_state.risk_scorer:
                        with st.spinner("Simulating impact..."):
                            modification = RuleModification(
                                rule_id=selected_rule_id,
                                modification_type=mod_type_enum,
                                parameters=parameters,
                                description=description
                            )
                            
                            impact = st.session_state.repair_engine.simulate_impact(
                                modification,
                                st.session_state.executor,
                                st.session_state.scenarios[:500],  # Use subset for speed
                                st.session_state.risk_scorer
                            )
                            
                            st.session_state.modification_results = impact
                            st.success("Impact simulation complete")
                    else:
                        st.error("Please run analysis in Discover Failures section first")
        
        with col2:
            st.markdown("**Simulation Results:**")
            
            if st.session_state.modification_results:
                impact = st.session_state.modification_results
                
                # Show recommendation
                st.info(impact['recommendation'])
                
                # Risk comparison
                st.markdown("**Risk Score Comparison:**")
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric(
                        "Before",
                        f"{impact['baseline']['composite_risk_score']:.3f}"
                    )
                
                with col_b:
                    st.metric(
                        "After",
                        f"{impact['modified']['composite_risk_score']:.3f}",
                        delta=f"{impact['changes']['risk_delta']:.3f}",
                        delta_color="inverse"
                    )
                
                with col_c:
                    severity_change = f"{impact['baseline']['overall_severity']} → {impact['modified']['overall_severity']}"
                    st.metric("Severity", severity_change)
                
                # Decision distribution changes
                st.markdown("**Decision Distribution Changes:**")
                
                shifts = impact['changes']['decision_shifts']
                shift_data = []
                for decision, values in shifts.items():
                    shift_data.append({
                        'Decision': decision,
                        'Before': values['before'],
                        'After': values['after'],
                        'Change': values['delta']
                    })
                
                st.dataframe(pd.DataFrame(shift_data))
                
                # Export modified rules
                if st.button("Export Modified Rules"):
                    modified_rules = st.session_state.repair_engine.apply_modification(
                        impact['modification']
                    )
                    st.session_state.repair_engine.export_modified_rules(
                        modified_rules,
                        '/tmp/modified_rules.json'
                    )
                    
                    with open('/tmp/modified_rules.json', 'r') as f:
                        rules_json = f.read()
                    
                    st.download_button(
                        label="Download Modified Rules",
                        data=rules_json,
                        file_name="modified_rules.json",
                        mime="application/json"
                    )
    
    with tab2:
        st.markdown("**Auto-Generated Suggestions**")
        
        if st.session_state.failure_detector and st.session_state.risk_scorer:
            if st.button("Generate Suggestions", type="primary"):
                with st.spinner("Analyzing issues..."):
                    suggestions = st.session_state.repair_engine.suggest_modifications(
                        st.session_state.failure_detector.detection_results,
                        st.session_state.risk_scorer.risk_scores
                    )
                    
                    st.session_state.suggested_modifications = suggestions
            
            if hasattr(st.session_state, 'suggested_modifications'):
                st.markdown(f"**{len(st.session_state.suggested_modifications)} suggestions generated:**")
                
                for i, suggestion in enumerate(st.session_state.suggested_modifications, 1):
                    with st.expander(f"Suggestion {i}: {suggestion.description}"):
                        st.markdown(f"**Modification Type:** {suggestion.modification_type.value}")
                        st.markdown(f"**Target Rule:** {suggestion.rule_id}")
                        st.json(suggestion.parameters)
                        
                        if st.button(f"Test This Suggestion", key=f"test_sug_{i}"):
                            if st.session_state.scenarios and st.session_state.executor:
                                impact = st.session_state.repair_engine.simulate_impact(
                                    suggestion,
                                    st.session_state.executor,
                                    st.session_state.scenarios[:500],
                                    st.session_state.risk_scorer
                                )
                                st.info(impact['recommendation'])
                                st.metric(
                                    "Risk Change",
                                    f"{impact['changes']['risk_delta']:.3f}",
                                    delta_color="inverse"
                                )
        else:
            st.info("Run failure detection analysis in Discover Failures section to generate suggestions")
    
    with tab3:
        st.markdown("**Compare Multiple Modifications**")
        
        if st.session_state.modification_results:
            impact = st.session_state.modification_results
            
            # Visualization comparing before/after
            comparison_data = {
                'Metric': ['Coverage Gap', 'Concentration', 'Composite Risk'],
                'Baseline': [
                    impact['baseline']['coverage_gap_rate'],
                    impact['baseline']['concentration_score'],
                    impact['baseline']['composite_risk_score']
                ],
                'Modified': [
                    impact['modified']['coverage_gap_rate'],
                    impact['modified']['concentration_score'],
                    impact['modified']['composite_risk_score']
                ]
            }
            
            df_comp = pd.DataFrame(comparison_data)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Baseline', x=df_comp['Metric'], y=df_comp['Baseline']))
            fig.add_trace(go.Bar(name='Modified', x=df_comp['Metric'], y=df_comp['Modified']))
            
            fig.update_layout(
                title="Before vs After Comparison",
                barmode='group',
                yaxis_title="Score",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Simulate a modification in the Manual Changes tab to see comparison")


def main():
    """Main application."""
    init_session_state()
    render_header()
    
    # Top Status Bar
    render_status_bar()
    
    # Minimal sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        section = st.radio(
            "Go to section",
            [
                "Overview",
                "Define System",
                "Stress Test",
                "Discover Failures",
                "Risk Dashboard",
                "Policy Repair"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("Policy Intelligence Engine v2.0")
    
    # Render selected section
    if section == "Overview":
        section_landing()
    elif section == "Define System":
        section_define_system()
    elif section == "Stress Test":
        section_stress_test()
    elif section == "Discover Failures":
        section_discover_failures()
    elif section == "Risk Dashboard":
        section_risk_dashboard()
    elif section == "Policy Repair":
        section_what_if()


if __name__ == "__main__":
    main()
