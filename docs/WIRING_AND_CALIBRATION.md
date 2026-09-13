# Wiring and Calibration

## Arduino UNO V3 wiring

| Component | Signal | Arduino |
|---|---|---|
| pH sensor module | Analog output | A0 |
| UV sensor module | Analog output | A1 |
| pH sensor module | VCC | module-rated supply |
| UV sensor module | VCC | module-rated supply |
| Sensors | GND | common GND |
| Optional isolated UV-C relay | Control | D7 |

Check the voltage requirements printed on your actual sensor modules before connecting them.

## UV sensor placement

For this project, the UV sensor is intended to measure **UV lamp intensity above the juice container**.

It is not intended to measure light absorption through the juice.

Keep the geometry repeatable between tests:
- same lamp-to-container distance
- same sensor height
- same sensor orientation
- same container location

## pH calibration

A two-point calibration is preferred.

If you obtain two known pH references:

- reference 1: voltage `V1`, pH `pH1`
- reference 2: voltage `V2`, pH `pH2`

then:

```text
slope = (pH2 - pH1) / (V2 - V1)
intercept = pH1 - slope * V1
```

Put the resulting values into:

```cpp
PH_SLOPE
PH_INTERCEPT
```

## UV calibration

Use a calibrated UV-C meter if you want an absolute UV intensity value.

Measure several points and fit:

```text
UV intensity = slope × sensor voltage + intercept
```

Then update:

```cpp
UV_SLOPE
UV_INTERCEPT
```

The dashboard can still use raw UV ADC values before full calibration.

## UV-C electrical safety

Do not power a UV-C lamp directly from an Arduino pin.

Use a properly rated, electrically isolated switching interface and a closed treatment chamber with appropriate interlocks. UV-C exposure can injure the eyes and skin.
