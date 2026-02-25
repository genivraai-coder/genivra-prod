import importlib
import sys

_mapping = [
    'train_logistic_regression',
    'predict_trial',
    'train_model',
    'predict_model',
    'rule_based_scorer',
]

for mod in _mapping:
    try:
        source = importlib.import_module(f'Models.{mod}')
        sys.modules[f'models.{mod}'] = source
    except Exception:
        pass

try:
    models_pkg = importlib.import_module('Models')
    for name in getattr(models_pkg, '__all__', []):
        try:
            globals()[name] = getattr(models_pkg, name)
        except Exception:
            pass
except Exception:
    pass
# Models package
# Contains model definitions, training logic, and inference utilities

try:
    from .rule_based_scorer import TrialScorer, score_trial, score_trials_batch
except ImportError:
    pass
