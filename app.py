# Wrapper to run the app directly from root
import os
import sys

# Change working directory to ensure paths inside subfolders work correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and execute the app code
with open("gainesville-events-map/app.py", "r", encoding="utf-8") as f:
    code = compile(f.read(), "gainesville-events-map/app.py", "exec")
    exec(code, globals())
