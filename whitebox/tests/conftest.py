"""Configuration for pytest — adds the code directory to sys.path."""

import sys
import os

# Add whitebox/code to path so `from moneypoly.xxx import ...` works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
