from __future__ import annotations
import math
import pandas as pd

def energy_table(uv, hpp, refrigeration, lab):
    rows = [
        ("UV-C lamps/chamber", float(uv)),
        ("HPP generator", float(hpp)),
        ("Cold storage refrigerator", float(refrigeration)),
        ("Measuring/lab devices", float(lab)),
    ]
    df = pd.DataFrame(rows, columns=["Component", "Energy (kWh/day)"])
    total = df["Energy (kWh/day)"].sum()
    return df, total

def pv_size(daily_kwh: float, peak_sun_hours: float, system_efficiency: float) -> float:
    if peak_sun_hours <= 0 or system_efficiency <= 0:
        return 0.0
    return float(daily_kwh) / (float(peak_sun_hours) * float(system_efficiency))

def panel_count(design_kw: float, panel_kw: float) -> int:
    if panel_kw <= 0:
        return 0
    return int(math.ceil(float(design_kw) / float(panel_kw)))
