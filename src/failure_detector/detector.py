"""
Failure & Instability Detector Module

This is the ML core of the system that identifies:
1. Anomalous decision patterns (using Isolation Forest / LOF)
2. Unknown failure modes (using clustering)
3. Decision instability (sensitivity to input perturbations)

Design Philosophy:
- ML is used for discovery, not prediction
- Focus on finding what humans didn't anticipate
- Explain every detection with evidence
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.spatial.distance import euclidean


class FailureDetector:
    """
    Detects anomalies, instabilities, and failure modes in decision patterns.
    
    Uses unsupervised ML techniques to discover:
    - Anomalous scenarios that lead to unexpected decisions
    - Clusters of similar failures
    - Instability zones where small changes cause large decision shifts
    """
    
    def __init__(self):
        """Initialize the failure detector."""
        self.anomaly_detector = None
        self.lof_detector = None
        self.cluster_model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.detection_results = {}
    
    def prepare_data(self, results_df: pd.DataFrame) -> np.ndarray:
        """
        Prepare execution results for ML analysis.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            
        Returns:
            Scaled feature matrix
        """
        # Extract feature columns (those starting with 'feature_')
        self.feature_columns = [col for col in results_df.columns if col.startswith('feature_')]
        
        if len(self.feature_columns) == 0:
            raise ValueError("No feature columns found in results")
        
        # Extract features and handle categorical variables
        X = results_df[self.feature_columns].copy()
        
        # Convert categorical to numeric using label encoding
        for col in X.columns:
            if X[col].dtype == 'object' or X[col].dtype.name == 'category':
                X[col] = pd.Categorical(X[col]).codes
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled
    
    def detect_anomalies(self, results_df: pd.DataFrame, 
                        contamination: float = 0.1,
                        method: str = 'isolation_forest') -> pd.DataFrame:
        """
        Detect anomalous scenarios using unsupervised anomaly detection.
        
        Anomalies represent scenarios that are significantly different from
        typical patterns - potential edge cases or failure modes.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            contamination: Expected proportion of anomalies (0-0.5)
            method: 'isolation_forest' or 'lof' (Local Outlier Factor)
            
        Returns:
            DataFrame with anomaly scores and flags
        """
        X_scaled = self.prepare_data(results_df)
        
        if method == 'isolation_forest':
            # Isolation Forest - good for global anomalies
            self.anomaly_detector = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            
            anomaly_labels = self.anomaly_detector.fit_predict(X_scaled)
            anomaly_scores = self.anomaly_detector.score_samples(X_scaled)
            
        elif method == 'lof':
            # Local Outlier Factor - good for local density anomalies
            self.lof_detector = LocalOutlierFactor(
                contamination=contamination,
                novelty=False,
                n_neighbors=20
            )
            
            anomaly_labels = self.lof_detector.fit_predict(X_scaled)
            anomaly_scores = self.lof_detector.negative_outlier_factor_
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Add results to dataframe
        results_with_anomalies = results_df.copy()
        results_with_anomalies['is_anomaly'] = (anomaly_labels == -1)
        results_with_anomalies['anomaly_score'] = anomaly_scores
        
        # Store results
        self.detection_results['anomalies'] = results_with_anomalies[
            results_with_anomalies['is_anomaly']
        ].copy()
        
        return results_with_anomalies
    
    def discover_failure_clusters(self, results_df: pd.DataFrame,
                                  eps: float = 0.5,
                                  min_samples: int = 5) -> pd.DataFrame:
        """
        Discover clusters of similar failure patterns using DBSCAN.
        
        Clusters represent groups of scenarios that lead to similar
        (potentially problematic) decisions. This helps identify
        systematic failure modes.
        
        Args:
            results_df: DataFrame from DecisionExecutor
            eps: Maximum distance between samples in a cluster
            min_samples: Minimum samples to form a dense region
            
        Returns:
            DataFrame with cluster assignments
        """
        X_scaled = self.prepare_data(results_df)
        
        # Apply DBSCAN clustering
        self.cluster_model = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = self.cluster_model.fit_predict(X_scaled)
        
        # Add cluster labels
        results_with_clusters = results_df.copy()
        results_with_clusters['cluster'] = cluster_labels
        
        # Analyze each cluster
        cluster_analysis = []
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # Noise points
                continue
            
            cluster_data = results_with_clusters[results_with_clusters['cluster'] == cluster_id]
            
            # Get decision distribution in cluster
            decision_dist = cluster_data['decision'].value_counts().to_dict()
            
            # Calculate cluster characteristics
            cluster_info = {
                'cluster_id': cluster_id,
                'size': len(cluster_data),
                'decisions': decision_dist,
                'dominant_decision': cluster_data['decision'].mode()[0],
                'avg_confidence': cluster_data['confidence'].mean(),
                'rules_involved': cluster_data['rule_id'].unique().tolist()
            }
            
            cluster_analysis.append(cluster_info)
        
        self.detection_results['clusters'] = pd.DataFrame(cluster_analysis)
        self.detection_results['cluster_assignments'] = results_with_clusters
        
        return results_with_clusters
    
    def detect_instability(self, decision_executor, 
                          base_scenarios: List[Dict],
                          n_perturbations: int = 10,
                          perturbation_magnitude: float = 0.05) -> List[Dict]:
        """
        Detect decision instability by perturbing scenarios.
        
        Instability occurs when small changes in inputs lead to large
        changes in decisions - a sign of rule conflicts or boundary issues.
        
        Args:
            decision_executor: DecisionExecutor instance
            base_scenarios: Scenarios to test for stability
            n_perturbations: Number of perturbations per scenario
            perturbation_magnitude: Size of perturbations
            
        Returns:
            List of instability reports
        """
        # Import here to avoid circular dependencies
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scenario_generator.generator import ScenarioGenerator, FeatureSpec
        
        instability_reports = []
        
        for i, base_scenario in enumerate(base_scenarios):
            # Get base decision
            base_result = decision_executor.rule_engine.execute(base_scenario)
            base_decision = base_result['decision']
            
            # Create feature specs from scenario
            feature_specs = []
            for key, value in base_scenario.items():
                if isinstance(value, (int, float)):
                    # Assume 20% range around current value for perturbation
                    min_val = value * 0.8
                    max_val = value * 1.2
                    spec_type = 'continuous' if isinstance(value, float) else 'discrete'
                    feature_specs.append(
                        FeatureSpec(name=key, type=spec_type, range=(min_val, max_val))
                    )
                else:
                    # Categorical - use current value only
                    feature_specs.append(
                        FeatureSpec(name=key, type='categorical', values=[value])
                    )
            
            # Generate perturbations
            generator = ScenarioGenerator(feature_specs)
            perturbed_scenarios = generator.generate_adversarial_perturbations(
                base_scenario, n_perturbations, perturbation_magnitude
            )
            
            # Test each perturbation
            decision_changes = []
            for j, perturbed in enumerate(perturbed_scenarios):
                perturbed_result = decision_executor.rule_engine.execute(perturbed)
                perturbed_decision = perturbed_result['decision']
                
                if perturbed_decision != base_decision:
                    # Calculate perturbation distance
                    distance = self._calculate_perturbation_distance(
                        base_scenario, perturbed
                    )
                    
                    decision_changes.append({
                        'perturbation_id': j,
                        'distance': distance,
                        'original_decision': base_decision,
                        'new_decision': perturbed_decision,
                        'original_rule': base_result['rule_id'],
                        'new_rule': perturbed_result['rule_id'],
                        'perturbed_scenario': perturbed
                    })
            
            # Calculate instability score
            instability_score = len(decision_changes) / n_perturbations
            
            if instability_score > 0:
                instability_reports.append({
                    'scenario_id': i,
                    'base_scenario': base_scenario,
                    'base_decision': base_decision,
                    'instability_score': instability_score,
                    'decision_changes': decision_changes,
                    'num_perturbations': n_perturbations
                })
        
        self.detection_results['instabilities'] = instability_reports
        
        return instability_reports
    
    def _calculate_perturbation_distance(self, scenario1: Dict, scenario2: Dict) -> float:
        """Calculate normalized distance between two scenarios."""
        distances = []
        
        for key in scenario1.keys():
            if key in scenario2:
                val1, val2 = scenario1[key], scenario2[key]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Normalize by value magnitude
                    max_val = max(abs(val1), abs(val2), 1e-10)
                    distances.append(abs(val1 - val2) / max_val)
                elif val1 != val2:
                    distances.append(1.0)  # Categorical difference
        
        return np.mean(distances) if distances else 0.0
    
    def find_high_impact_edges(self, results_df: pd.DataFrame,
                              decision_executor,
                              top_k: int = 10) -> List[Dict]:
        """
        Find high-impact edge cases - scenarios that are both anomalous
        and lead to unexpected decisions.
        
        Args:
            results_df: DataFrame from DecisionExecutor with anomaly detection
            decision_executor: DecisionExecutor instance
            top_k: Number of top edge cases to return
            
        Returns:
            List of high-impact edge case dictionaries
        """
        if 'is_anomaly' not in results_df.columns:
            results_df = self.detect_anomalies(results_df)
        
        # Filter anomalies
        anomalies = results_df[results_df['is_anomaly']].copy()
        
        if len(anomalies) == 0:
            return []
        
        # Calculate impact score based on:
        # 1. Anomaly score (how unusual)
        # 2. Confidence level (lower confidence = higher uncertainty)
        # 3. Decision rarity (rare decisions = higher impact)
        
        decision_counts = results_df['decision'].value_counts()
        total_scenarios = len(results_df)
        
        edge_cases = []
        for _, row in anomalies.iterrows():
            decision = row['decision']
            decision_rarity = 1 - (decision_counts.get(decision, 0) / total_scenarios)
            confidence_uncertainty = 1 - row['confidence']
            anomaly_severity = abs(row['anomaly_score'])
            
            # Composite impact score
            impact_score = (
                0.4 * anomaly_severity +
                0.3 * decision_rarity +
                0.3 * confidence_uncertainty
            )
            
            edge_case = {
                'scenario_id': row['scenario_id'],
                'decision': decision,
                'impact_score': impact_score,
                'anomaly_score': row['anomaly_score'],
                'confidence': row['confidence'],
                'decision_rarity': decision_rarity,
                'rule_id': row['rule_id']
            }
            
            # Add scenario features
            for col in self.feature_columns:
                edge_case[col.replace('feature_', '')] = row[col]
            
            edge_cases.append(edge_case)
        
        # Sort by impact score and return top k
        edge_cases.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return edge_cases[:top_k]
    
    def get_detection_summary(self) -> Dict:
        """
        Get summary of all detection results.
        
        Returns:
            Dictionary with detection statistics
        """
        summary = {}
        
        if 'anomalies' in self.detection_results:
            summary['total_anomalies'] = len(self.detection_results['anomalies'])
        
        if 'clusters' in self.detection_results:
            summary['total_clusters'] = len(self.detection_results['clusters'])
            summary['cluster_details'] = self.detection_results['clusters'].to_dict('records')
        
        if 'instabilities' in self.detection_results:
            summary['total_unstable_scenarios'] = len(self.detection_results['instabilities'])
            summary['avg_instability_score'] = np.mean([
                r['instability_score'] for r in self.detection_results['instabilities']
            ]) if self.detection_results['instabilities'] else 0
        
        return summary
