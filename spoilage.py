from __future__ import annotations
import pandas as pd
from config import CFG

def assess_status(ph: float, baseline_ph: float, storage_day: float | None = None) -> dict:
    """
    Prototype status heuristic.
    This is NOT a microbiological food-safety test.
    """
    if ph is None or baseline_ph is None or any(pd.isna(x) for x in [ph, baseline_ph]):
        return {
            "status": "No data",
            "level": "neutral",
            "ph_drift": None,
            "message": "A valid pH reading and baseline are required."
        }

    drift = abs(float(ph) - float(baseline_ph))
    status = "Normal"
    level = "good"
    reasons = []

    if drift >= CFG.ph_warning_drift:
        status = "Warning"
        level = "warning"
        reasons.append(f"pH drift is {drift:.2f}, above the warning threshold.")
    elif drift >= CFG.ph_monitor_drift:
        status = "Monitor"
        level = "monitor"
        reasons.append(f"pH drift is {drift:.2f}, so the batch should be monitored.")

    if storage_day is not None and not pd.isna(storage_day):
        day = float(storage_day)
        if day >= CFG.treated_warning_day:
            if level != "warning":
                status, level = "Warning", "warning"
            reasons.append("Storage time has reached the treated-batch observation range.")
        elif day >= CFG.treated_monitor_day and level == "good":
            status, level = "Monitor", "monitor"
            reasons.append("Storage time is approaching the treated-batch observation range.")

    if not reasons:
        reasons.append("pH remains close to the batch baseline in this prototype model.")

    return {
        "status": status,
        "level": level,
        "ph_drift": drift,
        "message": " ".join(reasons),
    }
