from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

from config import APP_TITLE, CFG
from data_utils import load_csv, baseline_ph, latest_valid, summary, normalize_columns
from serial_reader import available_ports, read_samples
from spoilage import assess_status
from energy import energy_table, pv_size, panel_count

BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = BASE / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-title">Smart Cold-Press Management System</div>
  <div class="hero-sub">Arduino-based pH & UV monitoring • Streamlit dashboard • solar-energy analysis</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Data source")
    mode = st.radio("Choose source", ["Demo data", "Upload CSV", "Arduino serial"], index=0)
    batch_type = st.selectbox("Batch type", ["UV-C treated", "Untreated / control"])
    st.caption("The status model is for prototype monitoring only.")

def get_data():
    if mode == "Demo data":
        path = BASE / "data" / ("sample_treated_run.csv" if batch_type == "UV-C treated" else "sample_untreated_run.csv")
        return load_csv(path), path.name

    if mode == "Upload CSV":
        up = st.sidebar.file_uploader("Upload run CSV", type=["csv"])
        if up is None:
            return pd.DataFrame(), None
        return load_csv(up), up.name

    ports = available_ports()
    if not ports:
        st.sidebar.warning("No serial ports detected.")
        return pd.DataFrame(), None

    port = st.sidebar.selectbox("Serial port", ports)
    baud = st.sidebar.selectbox("Baud rate", [115200, 9600], index=0)
    samples = st.sidebar.slider("Samples per read", 5, 100, 20, 5)
    if st.sidebar.button("Read Arduino samples", use_container_width=True):
        try:
            df = read_samples(port, baudrate=baud, samples=samples)
            if not df.empty:
                st.session_state["serial_df"] = df
        except Exception as exc:
            st.sidebar.error(str(exc))
    return st.session_state.get("serial_df", pd.DataFrame()), f"Serial: {port}"

df, source_name = get_data()

tabs = st.tabs(["Live Dashboard", "Run Comparison", "Solar Energy", "About"])

with tabs[0]:
    if df.empty:
        st.info("Choose demo data, upload a CSV file, or read the Arduino from the sidebar.")
    else:
        base_ph = baseline_ph(df)
        current_ph = latest_valid(df, "ph")
        uv_intensity = latest_valid(df, "uv_mw_cm2")
        uv_raw = latest_valid(df, "uv_raw")
        uv_on = latest_valid(df, "uv_on", False)
        storage_day = latest_valid(df, "storage_day")

        status = assess_status(current_ph, base_ph, storage_day if batch_type == "UV-C treated" else None)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current pH", "—" if current_ph is None else f"{float(current_ph):.2f}",
                  "baseline " + ("—" if base_ph is None else f"{base_ph:.2f}"))
        if uv_intensity is not None and not pd.isna(uv_intensity):
            c2.metric("UV intensity", f"{float(uv_intensity):.3f} mW/cm²")
        elif uv_raw is not None:
            c2.metric("UV sensor", f"{int(float(uv_raw))} ADC")
        else:
            c2.metric("UV sensor", "—")
        c3.metric("UV-C status", "ON" if bool(uv_on) else "OFF")
        c4.metric("Storage day", "—" if storage_day is None else f"{float(storage_day):.1f}")

        st.markdown(
            f'<div class="status-{status["level"]}">'
            f'Prototype batch status: {status["status"]}<br>'
            f'<span class="small-note">{status["message"]}</span></div>',
            unsafe_allow_html=True
        )

        st.write("")
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.subheader("pH trend")
            if "ph" in df.columns:
                plot = df[["elapsed_s", "ph"]].dropna().set_index("elapsed_s")
                st.line_chart(plot, y="ph", height=310)
            else:
                st.info("No pH column found.")

        with chart_cols[1]:
            st.subheader("UV trend")
            uv_col = "uv_mw_cm2" if "uv_mw_cm2" in df.columns and df["uv_mw_cm2"].notna().any() else "uv_raw"
            if uv_col in df.columns:
                plot = df[["elapsed_s", uv_col]].dropna().set_index("elapsed_s")
                st.line_chart(plot, y=uv_col, height=310)
            else:
                st.info("No UV column found.")

        with st.expander("Show run data"):
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download current run CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="cold_press_run.csv",
                mime="text/csv"
            )

        st.caption(f"Source: {source_name}")

with tabs[1]:
    st.subheader("Compare run files")
    uploads = st.file_uploader(
        "Upload two or more CSV run files",
        type=["csv"],
        accept_multiple_files=True,
        key="compare_uploads"
    )

    compare_frames = []
    if uploads:
        for up in uploads:
            try:
                x = load_csv(up)
                s = summary(x)
                s["file"] = up.name
                s["baseline_ph"] = baseline_ph(x)
                s["latest_ph"] = latest_valid(x, "ph")
                compare_frames.append(s)
            except Exception as exc:
                st.warning(f"{up.name}: {exc}")
    else:
        # Make the feature visible immediately with the two included samples.
        for fn in ["sample_treated_run.csv", "sample_untreated_run.csv"]:
            x = load_csv(BASE / "data" / fn)
            s = summary(x)
            s["file"] = fn
            s["baseline_ph"] = baseline_ph(x)
            s["latest_ph"] = latest_valid(x, "ph")
            compare_frames.append(s)

    if compare_frames:
        comp = pd.DataFrame(compare_frames).set_index("file")
        st.dataframe(comp.round(3), use_container_width=True)

        if {"baseline_ph", "latest_ph"}.issubset(comp.columns):
            st.subheader("Baseline vs latest pH")
            st.bar_chart(comp[["baseline_ph", "latest_ph"]], height=320)

    st.caption("Upload two or more run files to compare them side by side.")

with tabs[2]:
    st.subheader("Solar Energy Integration")
    st.write("The defaults below reflect the scaled-up UV-C + HPP energy model.")

    a, b = st.columns(2)
    with a:
        uv = st.number_input("UV-C chamber (kWh/day)", min_value=0.0, value=CFG.uv_kwh_day, step=0.001, format="%.3f")
        hpp = st.number_input("HPP generator (kWh/day)", min_value=0.0, value=CFG.hpp_kwh_day, step=0.1)
        refrigeration = st.number_input("Cold storage (kWh/day)", min_value=0.0, value=CFG.refrigeration_kwh_day, step=0.1)
        lab = st.number_input("Measuring/lab devices (kWh/day)", min_value=0.0, value=CFG.lab_kwh_day, step=0.01)
    with b:
        psh = st.number_input("Peak sun hours (h/day)", min_value=0.1, value=CFG.peak_sun_hours, step=0.1)
        efficiency = st.slider("Overall PV system efficiency", 0.30, 1.00, CFG.system_efficiency, 0.01)
        panel_w = st.number_input("Panel rating (W)", min_value=100, value=int(CFG.panel_kw * 1000), step=10)
        design_kw = st.number_input("Selected design PV size (kW)", min_value=0.1, value=CFG.design_pv_kw, step=0.1)

    e_df, total = energy_table(uv, hpp, refrigeration, lab)
    calculated = pv_size(total, psh, efficiency)
    n_panels = panel_count(design_kw, panel_w / 1000.0)

    m1, m2, m3 = st.columns(3)
    m1.metric("Daily demand", f"{total:.3f} kWh/day", f"≈ {round(total):.0f} kWh/day")
    m2.metric("Calculated PV minimum", f"{calculated:.2f} kW")
    m3.metric("Selected PV design", f"{design_kw:.1f} kW", f"{n_panels} × {panel_w} W panels")

    st.dataframe(e_df, use_container_width=True, hide_index=True)
    st.bar_chart(e_df.set_index("Component"), y="Energy (kWh/day)", height=300)

    st.info(
        "Design concept: approximately 1.7 kW PV for an estimated ~7 kWh/day system demand, "
        "using 5.5 peak-sun-hours/day and 75% overall system efficiency. "
        "Estimated practical installation area is about 14–16 m²."
    )

with tabs[3]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(str(BASE / "assets" / "logo.svg"), width=220)
    with c2:
        st.subheader("Project scope")
        st.markdown("""
- Masticating juicer prototype
- Arduino UNO V3 sensor acquisition
- pH monitoring
- UV-C lamp intensity monitoring
- Streamlit smart dashboard
- run-file logging and comparison
- prototype spoilage-status visualization
- renewable-energy / solar PV model
""")
    st.warning(
        "This dashboard is a monitoring prototype. pH and UV readings can support monitoring, "
        "but they do not by themselves prove microbiological safety."
    )
