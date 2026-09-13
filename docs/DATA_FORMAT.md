# CSV Data Format

The dashboard accepts CSV files with these preferred columns:

| Column | Meaning |
|---|---|
| timestamp | date/time of the reading |
| elapsed_s | seconds since run start |
| storage_day | age of the stored sample |
| ph | calibrated pH |
| ph_raw | Arduino ADC value |
| ph_voltage | pH module analog voltage |
| uv_mw_cm2 | calibrated UV intensity |
| uv_raw | Arduino ADC value |
| uv_voltage | UV module analog voltage |
| uv_on | 1/0 or true/false |

The dashboard also recognizes common aliases such as `day`, `days`, `uv`, and `uv_intensity`.

Example:

```csv
timestamp,elapsed_s,storage_day,ph,uv_mw_cm2,uv_on
2026-05-01 10:00:00,0,0,3.62,1.08,1
2026-05-01 10:00:01,1,0,3.61,1.11,1
```
