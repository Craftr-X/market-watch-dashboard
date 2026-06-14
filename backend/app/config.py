from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "market_watch.db"
DISCLAIMER = (
    "本系统仅用于市场学习和行情复盘，不构成投资建议。"
    "个股观察不代表买入建议，投资需自行决策并承担风险。"
)
