from __future__ import annotations
from io import BytesIO, StringIO
import pandas as pd
import numpy as np

CANONICAL = [
    "timestamp",
    "elapsed_s",
    "storage_day",
    "ph",
    "ph_raw",
    "ph_voltage",
    "uv_mw_cm2",
    "uv_raw",
    "uv_voltage",
    "uv_on",
]

ALIASES = {
    "time": "timestamp",
    "datetime": "timestamp",
    "day": "storage_day",
    "days": "storage_day",
    "ph_value": "ph",
    "uv": "uv_mw_cm2",
    "uv_intensity": "uv_mw_cm2",
    "uv_status": "uv_on",
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    out = out.rename(columns={c: ALIASES.get(c, c) for c in out.columns})

    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")

    numeric_cols = [
        "elapsed_s", "storage_day", "ph", "ph_raw", "ph_voltage",
        "uv_mw_cm2", "uv_raw", "uv_voltage"
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "uv_on" in out.columns:
        out["uv_on"] = out["uv_on"].map(
            lambda x: True if str(x).strip().lower() in {"1", "true", "on", "yes"}
            else False if str(x).strip().lower() in {"0", "false", "off", "no"}
            else x
        )

    if "elapsed_s" not in out.columns:
        if "timestamp" in out.columns and out["timestamp"].notna().any():
            first = out["timestamp"].dropna().iloc[0]
            out["elapsed_s"] = (out["timestamp"] - first).dt.total_seconds()
        else:
            out["elapsed_s"] = np.arange(len(out), dtype=float)

    return out

def load_csv(source) -> pd.DataFrame:
    return normalize_columns(pd.read_csv(source))

def baseline_ph(df: pd.DataFrame, n: int = 5) -> float | None:
    if "ph" not in df.columns:
        return None
    vals = df["ph"].dropna().head(n)
    if vals.empty:
        return None
    return float(vals.median())

def latest_valid(df: pd.DataFrame, col: str, default=None):
    if col not in df.columns:
        return default
    vals = df[col].dropna()
    if vals.empty:
        return default
    return vals.iloc[-1]

def summary(df: pd.DataFrame) -> dict:
    result = {"rows": len(df)}
    for col in ["ph", "uv_mw_cm2", "uv_raw"]:
        if col in df.columns and df[col].notna().any():
            result[f"{col}_mean"] = float(df[col].mean())
            result[f"{col}_min"] = float(df[col].min())
            result[f"{col}_max"] = float(df[col].max())
    if "storage_day" in df.columns and df["storage_day"].notna().any():
        result["storage_day_max"] = float(df["storage_day"].max())
    return result
