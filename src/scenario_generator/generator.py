"""
Scenario Generator Module

This module generates test scenarios to stress-test decision rules:
1. Normal cases: Representative scenarios from typical distributions
2. Boundary cases: Edge values that might trigger rule conflicts
3. Adversarial cases: Inputs designed to expose instability

Design Philosophy:
- Use simulation and constraint-based generation, not real data
- Focus on discovering edge cases and conflicts
- Generate scenarios that test rule boundaries systematically
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    """Types of scenarios to generate."""
    NORMAL = "normal"
    BOUNDARY = "boundary"
    ADVERSARIAL = "adversarial"
    RANDOM = "random"


@dataclass
class FeatureSpec:
    """
    Specification for a feature in the scenario space.
    
    Attributes:
        name: Feature name
        type: 'continuous', 'discrete', or 'categorical'
        range: For continuous/discrete - [min, max]
        values: For categorical - list of possible values
        distribution: Distribution type ('uniform', 'normal', 'exponential')
        mean: Mean for normal distribution
        std: Standard deviation for normal distribution
    """
    name: str
    type: str
    range: Optional[Tuple[float, float]] = None
    values: Optional[List[Any]] = None
    distribution: str = 'uniform'
    mean: Optional[float] = None
    std: Optional[float] = None


class ScenarioGenerator:
    """
    Generates diverse scenarios for stress-testing decision rules.
    
    This generator creates:
    - Normal cases from specified distributions
    - Boundary cases at feature limits
    - Adversarial cases designed to find conflicts
    """
    
    def __init__(self, feature_specs: List[FeatureSpec], random_seed: Optional[int] = None):
        """
        Initialize the scenario generator.
        
        Args:
            feature_specs: List of feature specifications
            random_seed: Random seed for reproducibility
        """
        self.feature_specs = {spec.name: spec for spec in feature_specs}
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def _generate_feature_value(self, spec: FeatureSpec, scenario_type: ScenarioType) -> Any:
        """
        Generate a single feature value based on type and specification.
        
        Args:
            spec: Feature specification
            scenario_type: Type of scenario being generated
            
        Returns:
            Generated feature value
        """
        if spec.type == 'categorical':
            if scenario_type == ScenarioType.ADVERSARIAL:
                # For adversarial, prefer edge cases in categorical values
                return np.random.choice(spec.values)
            else:
                return np.random.choice(spec.values)
        
        elif spec.type == 'continuous':
            min_val, max_val = spec.range
            
            if scenario_type == ScenarioType.BOUNDARY:
                # Generate boundary values
                boundary_points = [min_val, max_val, (min_val + max_val) / 2]
                # Add points slightly above/below boundaries
                epsilon = (max_val - min_val) * 0.01
                boundary_points.extend([min_val + epsilon, max_val - epsilon])
                return np.random.choice(boundary_points)
            
            elif scenario_type == ScenarioType.NORMAL:
                # Use specified distribution
                if spec.distribution == 'normal':
                    mean = spec.mean if spec.mean is not None else (min_val + max_val) / 2
                    std = spec.std if spec.std is not None else (max_val - min_val) / 6
                    value = np.random.normal(mean, std)
                    return np.clip(value, min_val, max_val)
                elif spec.distribution == 'exponential':
                    scale = (max_val - min_val) / 3
                    value = min_val + np.random.exponential(scale)
                    return np.clip(value, min_val, max_val)
                else:  # uniform
                    return np.random.uniform(min_val, max_val)
            
            else:  # RANDOM or ADVERSARIAL
                return np.random.uniform(min_val, max_val)
        
        elif spec.type == 'discrete':
            min_val, max_val = spec.range
            
            if scenario_type == ScenarioType.BOUNDARY:
                # Generate boundary values
                return np.random.choice([min_val, max_val, (min_val + max_val) // 2])
            else:
                return np.random.randint(min_val, max_val + 1)
        
        return None
    
    def generate(self, n: int, scenario_type: ScenarioType = ScenarioType.NORMAL) -> List[Dict]:
        """
        Generate n scenarios of the specified type.
        
        Args:
            n: Number of scenarios to generate
            scenario_type: Type of scenarios to generate
            
        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        
        for _ in range(n):
            scenario = {}
            for name, spec in self.feature_specs.items():
                scenario[name] = self._generate_feature_value(spec, scenario_type)
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_monte_carlo(self, n: int, feature_weights: Optional[Dict[str, float]] = None) -> List[Dict]:
        """
        Generate scenarios using Monte Carlo simulation with optional feature weighting.
        
        This method is useful for exploring the scenario space more thoroughly,
        particularly for finding rare combinations that might expose rule conflicts.
        
        Args:
            n: Number of scenarios to generate
            feature_weights: Optional weights for feature importance in sampling
            
        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        
        for _ in range(n):
            scenario = {}
            
            # Generate each feature with weighted probability if specified
            for name, spec in self.feature_specs.items():
                # Mix of different generation strategies
                strategy = np.random.choice(['normal', 'boundary', 'random'], 
                                          p=[0.6, 0.2, 0.2])
                
                if strategy == 'normal':
                    scenario[name] = self._generate_feature_value(spec, ScenarioType.NORMAL)
                elif strategy == 'boundary':
                    scenario[name] = self._generate_feature_value(spec, ScenarioType.BOUNDARY)
                else:
                    scenario[name] = self._generate_feature_value(spec, ScenarioType.RANDOM)
            
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_grid_search(self, resolution: int = 5) -> List[Dict]:
        """
        Generate scenarios using grid search across feature space.
        
        This creates a systematic grid of scenarios, useful for finding
        decision boundaries and conflicts systematically.
        
        Args:
            resolution: Number of points per feature dimension
            
        Returns:
            List of scenario dictionaries
            
        Note:
            This can generate a large number of scenarios (resolution^num_features).
            Use with caution for high-dimensional feature spaces.
        """
        # Create grid points for each feature
        feature_grids = {}
        
        for name, spec in self.feature_specs.items():
            if spec.type == 'continuous':
                min_val, max_val = spec.range
                feature_grids[name] = np.linspace(min_val, max_val, resolution)
            elif spec.type == 'discrete':
                min_val, max_val = spec.range
                feature_grids[name] = np.linspace(min_val, max_val, resolution, dtype=int)
            elif spec.type == 'categorical':
                feature_grids[name] = spec.values[:resolution]  # Take first n values
        
        # Generate all combinations
        scenarios = []
        self._generate_grid_recursive(feature_grids, list(self.feature_specs.keys()), 0, {}, scenarios)
        
        return scenarios
    
    def _generate_grid_recursive(self, grids: Dict, features: List[str], 
                                 index: int, current: Dict, results: List[Dict]):
        """Helper method for recursive grid generation."""
        if index >= len(features):
            results.append(current.copy())
            return
        
        feature = features[index]
        for value in grids[feature]:
            current[feature] = value
            self._generate_grid_recursive(grids, features, index + 1, current, results)
    
    def generate_adversarial_perturbations(self, base_scenario: Dict, 
                                          n_perturbations: int = 10,
                                          perturbation_magnitude: float = 0.1) -> List[Dict]:
        """
        Generate adversarial perturbations of a base scenario.
        
        This is useful for testing decision instability - small changes in input
        should not lead to drastically different decisions in a robust system.
        
        Args:
            base_scenario: Base scenario to perturb
            n_perturbations: Number of perturbed scenarios to generate
            perturbation_magnitude: Relative magnitude of perturbations (0-1)
            
        Returns:
            List of perturbed scenarios
        """
        perturbed_scenarios = []
        
        for _ in range(n_perturbations):
            perturbed = {}
            
            for name, value in base_scenario.items():
                spec = self.feature_specs[name]
                
                if spec.type == 'continuous':
                    min_val, max_val = spec.range
                    range_size = max_val - min_val
                    noise = np.random.normal(0, perturbation_magnitude * range_size)
                    perturbed[name] = np.clip(value + noise, min_val, max_val)
                
                elif spec.type == 'discrete':
                    min_val, max_val = spec.range
                    range_size = max_val - min_val
                    # Randomly add/subtract 1-2 steps
                    if np.random.random() < 0.3:  # 30% chance of perturbation
                        delta = np.random.choice([-2, -1, 1, 2])
                        perturbed[name] = int(np.clip(value + delta, min_val, max_val))
                    else:
                        perturbed[name] = value
                
                elif spec.type == 'categorical':
                    # Randomly flip to different category with low probability
                    if np.random.random() < 0.2:  # 20% chance of change
                        perturbed[name] = np.random.choice(spec.values)
                    else:
                        perturbed[name] = value
            
            perturbed_scenarios.append(perturbed)
        
        return perturbed_scenarios
    
    def generate_edge_cases(self, n_per_feature: int = 5) -> List[Dict]:
        """
        Generate edge cases that test extreme values for each feature.
        
        Args:
            n_per_feature: Number of edge case scenarios per feature
            
        Returns:
            List of edge case scenarios
        """
        edge_scenarios = []
        
        # For each feature, generate scenarios with extreme values
        for target_feature, target_spec in self.feature_specs.items():
            
            for _ in range(n_per_feature):
                scenario = {}
                
                for name, spec in self.feature_specs.items():
                    if name == target_feature:
                        # Use extreme value for target feature
                        if spec.type == 'continuous' or spec.type == 'discrete':
                            # Choose min or max
                            scenario[name] = np.random.choice(spec.range)
                        elif spec.type == 'categorical':
                            # Choose first or last value
                            scenario[name] = np.random.choice([spec.values[0], spec.values[-1]])
                    else:
                        # Use normal values for other features
                        scenario[name] = self._generate_feature_value(spec, ScenarioType.NORMAL)
                
                edge_scenarios.append(scenario)
        
        return edge_scenarios
    
    def get_feature_summary(self) -> Dict:
        """
        Get summary of feature specifications.
        
        Returns:
            Dictionary with feature statistics
        """
        return {
            'total_features': len(self.feature_specs),
            'continuous_features': sum(1 for s in self.feature_specs.values() if s.type == 'continuous'),
            'discrete_features': sum(1 for s in self.feature_specs.values() if s.type == 'discrete'),
            'categorical_features': sum(1 for s in self.feature_specs.values() if s.type == 'categorical'),
            'features': {
                name: {
                    'type': spec.type,
                    'range': spec.range,
                    'values': spec.values,
                    'distribution': spec.distribution
                }
                for name, spec in self.feature_specs.items()
            }
        }
