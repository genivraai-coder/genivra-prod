import importlib
import sys

_mapping = [
    'build_features',
    'utils',
]

for mod in _mapping:
    try:
        source = importlib.import_module(f'Features.{mod}')
        sys.modules[f'features.{mod}'] = source
    except Exception:
        # if import fails, skip - original package may not exist in some contexts
        pass

# Expose top-level names from Features if available
try:
    feat_pkg = importlib.import_module('Features')
    for name in getattr(feat_pkg, '__all__', []):
        try:
            globals()[name] = getattr(feat_pkg, name)
        except Exception:
            pass
except Exception:
    pass
from .feature_engineering import create_features, load_features
from .feature_selection import select_features

__all__ = [
    "create_features",
    "load_features",
    "select_features",
]