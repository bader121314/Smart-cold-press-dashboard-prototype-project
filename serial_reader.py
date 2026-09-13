from __future__ import annotations
import time
import pandas as pd
from io import StringIO

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

EXPECTED = [
    "device_ms", "ph_raw", "ph_voltage", "ph",
    "uv_raw", "uv_voltage", "uv_mw_cm2", "uv_on"
]

def available_ports():
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports()]

def read_samples(port: str, baudrate: int = 115200, samples: int = 20, timeout: float = 2.0):
    if serial is None:
        raise RuntimeError("pyserial is not installed.")
    rows = []
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        time.sleep(1.5)
        ser.reset_input_buffer()
        deadline = time.time() + max(5, samples * 2)
        while len(rows) < samples and time.time() < deadline:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line or line.lower().startswith("device_ms"):
                continue
            parts = [x.strip() for x in line.split(",")]
            if len(parts) != len(EXPECTED):
                continue
            rows.append(parts)

    if not rows:
        return pd.DataFrame(columns=EXPECTED)

    df = pd.DataFrame(rows, columns=EXPECTED)
    numeric = [c for c in EXPECTED if c != "uv_on"]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["uv_on"] = pd.to_numeric(df["uv_on"], errors="coerce").fillna(0).astype(int).astype(bool)
    df["elapsed_s"] = (df["device_ms"] - df["device_ms"].iloc[0]) / 1000.0
    df["timestamp"] = pd.Timestamp.now() - pd.to_timedelta(df["elapsed_s"].max() - df["elapsed_s"], unit="s")
    return df
