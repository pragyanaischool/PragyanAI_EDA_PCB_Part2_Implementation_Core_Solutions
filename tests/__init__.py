"""
PragyanAI Implementation Core - Test Suite
This package contains the Quality Control logic for:
1. Component Mapping (test_logic.py)
2. Electrical Connectivity (test_connectivity.py)
3. Procurement & BOM (test_bom.py)
"""

import os
import sys

# Ensure the root directory is in the sys.path so tests can import from 'core_engine'
# This prevents "ModuleNotFoundError" when running pytest from the terminal.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
