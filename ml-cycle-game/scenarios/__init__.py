"""
Scenarios package for ML Cycle Game platform.

This package provides:
- Base scenario classes
- Download configuration base classes
"""

from .base import BaseScenario
from .download_config import BaseDownloadConfig

# Available scenario classes
AVAILABLE_SCENARIOS = []

def register_scenario(scenario_class):
    """Register a scenario class."""
    AVAILABLE_SCENARIOS.append(scenario_class)

def list_scenarios():
    """List all available scenario classes."""
    return AVAILABLE_SCENARIOS.copy()

# Auto-register available scenarios
try:
    from .house_price_prediction.scenario import HousePricePredictionScenario
    register_scenario(HousePricePredictionScenario)
except ImportError:
    pass

__all__ = [
    "BaseScenario",
    "BaseDownloadConfig", 
    "register_scenario",
    "list_scenarios",
]
