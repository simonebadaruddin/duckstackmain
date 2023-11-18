"""Start Python module search at project root"""

# Help Python find the module(s) we want to test,
# telling it that search paths start one folder "up" in the hierarchy
import sys, os
this_folder = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(this_folder, "..")))
