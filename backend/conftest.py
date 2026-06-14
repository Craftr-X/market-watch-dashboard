import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `from app.xxx import ...` works
sys.path.insert(0, str(Path(__file__).resolve().parent))
