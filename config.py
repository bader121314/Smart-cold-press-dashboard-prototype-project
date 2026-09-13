from dataclasses import dataclass

APP_TITLE = "Smart Cold-Press Management System"

@dataclass(frozen=True)
class DashboardConfig:
    # Prototype monitoring thresholds.
    ph_monitor_drift: float = 0.15
    ph_warning_drift: float = 0.30
    treated_monitor_day: float = 8.0
    treated_warning_day: float = 10.0

    # Solar model defaults.
    uv_kwh_day: float = 0.005
    hpp_kwh_day: float = 1.7
    refrigeration_kwh_day: float = 4.8
    lab_kwh_day: float = 0.07
    peak_sun_hours: float = 5.5
    system_efficiency: float = 0.75
    design_pv_kw: float = 1.7
    panel_kw: float = 0.55

CFG = DashboardConfig()
