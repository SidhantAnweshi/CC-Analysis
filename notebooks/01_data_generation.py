"""
Notebook 01 — Data Generation
Run this ONLY if you want to regenerate data from scratch.
The run_pipeline.py script handles this automatically.
"""
# Equivalent of running: python scripts/generate_data.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), "scripts"))
# (If running from notebooks/) 
sys.path.insert(0, os.path.join(os.getcwd(), "..", "scripts"))

import generate_data
generate_data.main()
