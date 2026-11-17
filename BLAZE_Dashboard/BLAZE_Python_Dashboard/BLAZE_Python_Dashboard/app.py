"""BLAZE research dashboard (simulation-only Streamlit prototype)."""
from __future__ import annotations

import html
import random
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import (
    BAND_HIGH, BAND_LOW,
    init_db, add_reading, latest_reading, recent_readings, clear_telemetry,
    start_session, active_session, stop_session, all_sessions,
)

st.set_page_config(page_title="BLAZE | Research Dashboard", page_icon="🔥",
                   layout="wide")


@st.cache_resource
def _boot() -> bool:
    init_db()
    return True


_boot()

# ------------------------------------------------------------------ palette
CREAM = "#FFF3E3"
MUTED = "#B8A898"
EMBER = "#FF5A1F"
FLAME = "#FFB020"
LEAF = "#3DDC84"
HOT = "#FF3B4E"
GRID = "rgba(255,243,227,0.08)"

AXIS_MAX = 550.0
AMBIENT = 25.0
LOCAL_TZ = datetime.now().astimezone().tzinfo

# ---------------------------------------------------------------------- CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=DM+Sans:wght@400;500;600&display=swap');

:root{
  --char:#17120F; --coal:#231C17; --ash:#2E251F; --line:#3D3027;
  --cream:#FFF3E3; --muted:#B8A898;
  --ember:#FF5A1F; --flame:#FFB020; --leaf:#3DDC84; --hot:#FF3B4E;
}
.stApp{
  font-family:'DM Sans',system-ui,sans-serif;
  background:
    radial-gradient(1100px 520px at 8% -10%, rgba(255,90,31,.22), transparent 60%),
    radial-gradient(900px 500px at 100% 110%, rgba(61,220,132,.14), transparent 60%),
    var(--char);
}
h1,h2,h3{font-family:'Bricolage Grotesque','DM Sans',sans-serif !important;
  letter-spacing:-0.01em; color:var(--cream);}
.block-container{padding-top:2rem; max-width:1200px;}
[data-testid="stSidebar"]{background:#110D0A; border-right:1px solid rgba(255,90,31,.28);}

/* hero */
.hero{display:flex; align-items:center; gap:18px; margin:2px 0 16px;}
.hero-mark{font-size:2.8rem; filter:drop-shadow(0 0 18px rgba(255,90,31,.75));}
.hero-title{font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:3.1rem;
  line-height:1; background:linear-gradient(90deg,var(--flame),var(--ember) 55%,var(--hot));
  -webkit-background-clip:text; background-clip:text; color:transparent;}
.hero-sub{color:var(--muted); margin-top:6px; font-size:.98rem;}
.side-brand{font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:1.7rem;
  background:linear-gradient(90deg,var(--flame),var(--ember));
  -webkit-background-clip:text; background-clip:text; color:transparent;}

/* notice */
.notice{background:rgba(255,176,32,.09); border:1px solid rgba(255,176,32,.35);
  border-left:4px solid var(--flame); border-radius:10px; padding:11px 14px;
  color:#FFE2B0; font-size:.92rem; margin-bottom:18px;}

/* metric cards */
.card{background:linear-gradient(180deg,var(--coal),#1C1612); border:1px solid var(--line);
  border-radius:14px; padding:18px 18px 14px; min-height:118px; position:relative; overflow:hidden;}
.card::before{content:""; position:absolute; inset:0 0 auto 0; height:4px;
  background:var(--tone); box-shadow:0 0 18px var(--tone);}
.card .label{color:var(--muted); font-size:.88rem;}
.card .value{font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:2.05rem;
  color:var(--tone); margin-top:4px; line-height:1.1;}
.card .sub{color:var(--muted); font-size:.82rem; margin-top:6px;}
.tone-flame{--tone:var(--flame)} .tone-leaf{--tone:var(--leaf)}
.tone-ember{--tone:var(--ember)} .tone-hot{--tone:var(--hot)} .tone-neutral{--tone:#E8D9C6}

/* status chips */
.chip{display:flex; align-items:center; gap:10px; background:var(--coal);
  border:1px solid var(--line); border-radius:999px; padding:8px 14px; margin-bottom:8px;
  font-size:.9rem; color:var(--cream);}
.dot{width:10px; height:10px; border-radius:50%; background:var(--c);
  box-shadow:0 0 10px var(--c); flex:none;}
.dot-leaf{--c:var(--leaf)} .dot-flame{--c:var(--flame)} .dot-hot{--c:var(--hot)}

/* thermal strip */
.thermo{background:var(--coal); border:1px solid var(--line); border-radius:14px;
  padding:50px 24px 40px; margin:18px 0;}
.thermo-track{position:relative; height:16px; display:flex; border-radius:999px;}
.z{height:100%}
.z-cool{background:linear-gradient(90deg,#5b3a12,var(--flame)); border-radius:999px 0 0 999px}
.z-band{background:linear-gradient(90deg,#1f9d5a,var(--leaf))}
.z-hot{background:linear-gradient(90deg,var(--ember),var(--hot)); border-radius:0 999px 999px 0}
.marker{position:absolute; top:-9px; width:4px; height:34px; transform:translateX(-50%);
  background:var(--cream); border-radius:3px; box-shadow:0 0 14px rgba(255,243,227,.95);}
.marker span{position:absolute; bottom:40px; left:50%; transform:translateX(-50%);
  background:var(--cream); color:var(--char); font-weight:700; padding:2px 9px;
  border-radius:7px; white-space:nowrap; font-size:.9rem;}
.tick{position:absolute; top:26px; transform:translateX(-50%); font-size:.78rem; color:var(--muted);}
.thermo-note{color:var(--muted); font-size:.9rem; margin-top:34px;}

/* buttons */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button{
  border-radius:10px; border:1px solid var(--line); background:var(--ash);
  color:var(--cream); font-weight:600; transition:border-color .15s, color .15s;}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover{
  border-color:var(--ember); color:var(--flame);}
.stButton>button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"]{
  background:linear-gradient(90deg,var(--ember),var(--flame)); color:#1b0f07; border:none;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------ session state
for key, default in {
    "sim_temperature": 285.0,
    "sim_valve_open": True,
    "sim_running": True,
    "sim_fault": False,
    "last_alert": "",
    "chart_points": 180,
}.items():
    st.session_state.setdefault(key, default)

ss = st.session_state


# ------------------------------------------------------------------ helpers
def H(markup: str) -> None:
    """Render HTML without markdown mistaking indented lines for code blocks."""
    st.markdown("".join(line.strip() for line in markup.splitlines()),
                unsafe_allow_html=True)


def metric_card(label, value, sub="", tone="neutral") -> None:
    H(f'<div class="card tone-{tone}"><div class="label">{html.escape(str(label))}</div>'
      f'<div class="value">{html.escape(str(value))}</div>'
      f'<div class="sub">{html.escape(str(sub))}</div></div>')


def chip(text, color="leaf") -> None:
    H(f'<div class="chip"><i class="dot dot-{color}"></i>{html.escape(text)}</div>')


def zone_of(temp):
    if temp is None or pd.isna(temp):
        return "fault"
    if temp < BAND_LOW:
        return "warm"
    if temp < BAND_HIGH:
        return "band"
    return "hot"


ZONE_TONE = {"warm": "flame", "band": "leaf", "hot": "ember", "fault": "hot"}
ZONE_TEXT = {"warm": "Below reference band", "band": "Inside reference band",
             "hot": "Above reference band", "fault": "No valid reading"}


def thermal_strip(temp) -> None:
    pct = lambda v: v / AXIS_MAX * 100  # noqa: E731
    ticks = "".join(
        f'<div class="tick" style="left:{pct(v):.2f}%">{v}°</div>'
        for v in (0, 100, 200, 300, 400, 500)
    )
    if temp is None or pd.isna(temp):
        marker, note = "", "No valid temperature. A real controller should close the valve here."
    else:
        pos = max(0.0, min(100.0, pct(temp)))
        marker = f'<div class="marker" style="left:{pos:.2f}%"><span>{temp:.0f}°C</span></div>'
        note = ZONE_TEXT[zone_of(temp)]
    H(f'<div class="thermo"><div class="thermo-track">'
      f'<div class="z z-cool" style="width:{pct(BAND_LOW):.2f}%"></div>'
      f'<div class="z z-band" style="width:{pct(BAND_HIGH - BAND_LOW):.2f}%"></div>'
      f'<div class="z z-hot" style="width:{pct(AXIS_MAX - BAND_HIGH):.2f}%"></div>'
      f'{marker}{ticks}</div><div class="thermo-note">{html.escape(note)}</div></div>')


def localize(series: pd.Series) -> pd.Series:
    ts = pd.to_datetime(series, utc=True, errors="coerce", format="ISO8601")
    return ts.dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)


def fmt_duration(seconds) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"


def style_fig(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CREAM, family="DM Sans, sans-serif"),
        hovermode="x unified", showlegend=False,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


# ---------------------------------------------------------------- simulator
def simulator_tick() -> None:
    """Advance the SOFTWARE simulator by one sample and store it.

    Mirrors the documented threshold rules for display purposes only.
    Nothing here talks to hardware.
    """
    if ss.sim_fault:
        # Open thermocouple: no valid temperature, valve fails closed.
        ss.sim_valve_open = False
        add_reading(None, "FAULT", "SHUTOFF")
        return
    if not ss.sim_running:
        return  # paused: do not write new rows

    t = ss.sim_temperature
    if ss.sim_valve_open:
        t += random.uniform(2.0, 7.0)    # heating
    else:
        t -= random.uniform(1.5, 4.0)    # cooling
    t = max(AMBIENT, t + random.gauss(0, 0.4))
    ss.sim_temperature = t

    # Decide valve position for the NEXT interval (small overshoot is realistic).
    if t >= BAND_HIGH:
        ss.sim_valve_open = False
        state = "SHUTOFF"
    elif t < BAND_LOW:
        ss.sim_valve_open = True
        state = "HEATING"
    else:
        state = "HOLD"
    add_reading(t, "NORMAL", state)


def _run():
    ss.sim_running, ss.sim_fault = True, False


def _pause():
    ss.sim_running = False


def _fault():
    ss.sim_fault, ss.sim_running = True, False


def _reset():
    ss.sim_temperature, ss.sim_valve_open = 285.0, True
    ss.sim_running, ss.sim_fault, ss.last_alert = True, False, ""


# ------------------------------------------------------------------ sidebar
PAGES = {
    "Dashboard": "🔥  Dashboard",
    "Session logging": "🌿  Session logging",
    "History & export": "📈  History & export",
    "Settings": "⚙️  Settings",
    "About": "ℹ️  About",
}
with st.sidebar:
    H('<div class="side-brand">BLAZE</div>')
st.sidebar.caption("Research monitoring prototype")
page = st.sidebar.radio("Navigate", list(PAGES), format_func=PAGES.get,
                        label_visibility="collapsed")
st.sidebar.divider()
with st.sidebar:
    chip("Data: software simulator", "flame")
    chip("Valve and burner: not connected", "hot")

# ------------------------------------------------------------------- header
H('<div class="hero"><div class="hero-mark">🔥</div><div>'
  '<div class="hero-title">BLAZE</div>'
  '<div class="hero-sub">Biochar from Leaf-Straw Biomass via Automated Zonal Engineering</div>'
  '</div></div>')
H('<div class="notice"><b>Simulation only.</b> This app does not connect to or control a '
  'burner, LPG valve, kiln, or any high-temperature equipment. The 300–500 °C band is a '
  'display reference, not an operating target or safety limit. Never use this dashboard '
  'as a safety system.</div>')


# --------------------------------------------------------------- dashboard
def page_dashboard() -> None:
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Simulator controls")
        st.caption("These buttons change only the software simulator.")
        c1, c2 = st.columns(2)
        c1.button("▶  Run simulator", on_click=_run, type="primary", width="stretch")
        c2.button("■  Pause", on_click=_pause, width="stretch")
        c3, c4 = st.columns(2)
        c3.button("⚠  Simulate sensor fault", on_click=_fault, width="stretch")
        c4.button("↺  Reset demo", on_click=_reset, width="stretch")
    with right:
        st.subheader("Connections")
        chip("Data source: local simulator", "leaf")
        chip("ESP32 link: not configured", "flame")
        chip("Valve and burner: disconnected by design", "hot")

    @st.fragment(run_every="2s")
    def live_panel() -> None:
        simulator_tick()
        latest = latest_reading()
        st.divider()
        st.subheader("Live monitoring")
        if latest is None:
            st.info("No readings yet. Press Run simulator to start streaming demo data.")
            return

        temp, status, state = latest["temperature"], latest["sensor_status"], latest["state"]
        z = zone_of(temp)

        alert_key = "fault" if status == "FAULT" else ("shutoff" if state == "SHUTOFF" else "")
        if alert_key and alert_key != ss.last_alert:
            st.toast("Simulated sensor fault" if alert_key == "fault"
                     else "Simulated shutoff: temperature reached the upper threshold",
                     icon="⚠️")
        ss.last_alert = alert_key

        a, b, c, d = st.columns(4)
        with a:
            metric_card("Temperature", "—" if temp is None else f"{temp:.1f} °C",
                        ZONE_TEXT[z], ZONE_TONE[z])
        with b:
            metric_card("Controller state", state.title(),
                        "Paused" if not ss.sim_running and not ss.sim_fault else "Simulated",
                        ZONE_TONE[z])
        with c:
            ok = status == "NORMAL"
            metric_card("Sensor", "OK" if ok else "Fault",
                        "Thermocouple (simulated)", "leaf" if ok else "hot")
        with d:
            metric_card("Valve", "Open" if ss.sim_valve_open else "Closed",
                        "Simulated, nothing attached",
                        "flame" if ss.sim_valve_open else "neutral")

        thermal_strip(temp)

        df = pd.DataFrame(recent_readings(ss.chart_points))
        if df.empty:
            return
        df["created_at"] = localize(df["created_at"])
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
        valid = df.dropna(subset=["temperature"])

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            metric_card("Peak in window",
                        f"{valid['temperature'].max():.1f} °C" if not valid.empty else "—",
                        f"Last {len(df)} samples", "ember")
        with s2:
            metric_card("Average",
                        f"{valid['temperature'].mean():.1f} °C" if not valid.empty else "—",
                        "Valid readings only", "flame")
        with s3:
            in_band = ((valid["temperature"] >= BAND_LOW)
                       & (valid["temperature"] < BAND_HIGH)).mean() * 100 if not valid.empty else None
            metric_card("Time in band", "—" if in_band is None else f"{in_band:.0f}%",
                        "300–500 °C reference", "leaf")
        with s4:
            faults = int((df["sensor_status"] == "FAULT").sum())
            metric_card("Sensor faults", faults, "In this window",
                        "hot" if faults else "neutral")

        fig = go.Figure()
        fig.add_hrect(y0=BAND_LOW, y1=BAND_HIGH, fillcolor="rgba(61,220,132,0.12)",
                      line_width=0, annotation_text="Reference band",
                      annotation_position="top left",
                      annotation_font=dict(color=LEAF, size=12))
        fig.add_hline(y=BAND_HIGH, line=dict(color=HOT, width=1, dash="dot"))
        fig.add_trace(go.Scatter(
            x=df["created_at"], y=df["temperature"], mode="lines",
            line=dict(color=EMBER, width=3, shape="spline", smoothing=0.4),
            fill="tozeroy", fillcolor="rgba(255,90,31,0.12)",
            connectgaps=False, name="Temperature",
            hovertemplate="%{y:.1f} °C<extra></extra>",
        ))
        if not valid.empty:
            fig.add_trace(go.Scatter(
                x=[valid["created_at"].iloc[-1]], y=[valid["temperature"].iloc[-1]],
                mode="markers", marker=dict(color=FLAME, size=11,
                                            line=dict(color=CREAM, width=2)),
                hoverinfo="skip"))
        fault_rows = df[df["sensor_status"] == "FAULT"]
        if not fault_rows.empty:
            fig.add_trace(go.Scatter(
                x=fault_rows["created_at"], y=[8] * len(fault_rows), mode="markers",
                marker=dict(color=HOT, size=9, symbol="x"),
                hovertemplate="Sensor fault<extra></extra>"))
        style_fig(fig, 380)
        fig.update_yaxes(range=[0, AXIS_MAX + 10], title="Temperature (°C)")
        st.plotly_chart(fig, width="stretch", theme=None,
                        config={"displayModeBar": False})

        st.subheader("Recent readings")
        show = df.tail(8).iloc[::-1].copy()
        show["created_at"] = show["created_at"].dt.strftime("%H:%M:%S")
        show = show[["created_at", "temperature", "sensor_status", "state", "source"]]
        show.columns = ["Time", "Temperature", "Sensor", "State", "Source"]
        st.dataframe(show, width="stretch", hide_index=True, column_config={
            "Temperature": st.column_config.NumberColumn(format="%.1f °C")})

    live_panel()


# --------------------------------------------------------- session logging
def sessions_view(raw: pd.DataFrame) -> pd.DataFrame:
    for col in ("mass_in_g", "mass_out_g", "yield_percent", "duration_seconds",
                "peak_temperature", "seconds_in_reference_band"):
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    view = pd.DataFrame({
        "Batch": raw["batch_name"],
        "Feedstock": raw["feedstock"],
        "Mass in (g)": raw["mass_in_g"],
        "Biochar out (g)": raw["mass_out_g"],
        "Yield (%)": raw["yield_percent"],
        "Duration (min)": raw["duration_seconds"] / 60,
        "Peak (°C)": raw["peak_temperature"],
        "Minutes in band": raw["seconds_in_reference_band"] / 60,
        "Started": localize(raw["started_at"]).dt.strftime("%Y-%m-%d %H:%M"),
        "Notes": raw["notes"],
    })
    return view


def page_sessions() -> None:
    st.subheader("Batch and session logging")
    st.caption("Record research metadata. No physical process is started or stopped here.")
    st.caption("Peak temperature and time in band are computed from readings stored while "
               "the Dashboard page was open.")
    current = active_session()

    if current is None:
        with st.form("start_batch"):
            batch_name = st.text_input("Batch ID", placeholder="e.g. BLAZE-TEST-001")
            feedstock = st.selectbox("Feedstock type", [
                "Dry leaves", "Rice straw", "Mixed plant residue", "Other / not specified"])
            mass_in = st.number_input("Initial feedstock mass (g)", min_value=0.0,
                                      max_value=100000.0, value=100.0, step=10.0)
            notes = st.text_area("Research notes",
                                 placeholder="Sample description, moisture, observations…")
            submitted = st.form_submit_button("Start logging session", type="primary")
        if submitted:
            if not batch_name.strip():
                st.error("Enter a batch ID to start a session.")
            elif mass_in <= 0:
                st.error("Initial mass must be greater than 0 g to calculate yield.")
            else:
                try:
                    start_session(batch_name.strip(), feedstock, mass_in, notes)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.rerun()
    else:
        started = datetime.fromisoformat(current["started_at"])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        a, b, c = st.columns(3)
        with a:
            metric_card("Active batch", current["batch_name"], current["feedstock"], "leaf")
        with b:
            metric_card("Initial mass", f"{current['mass_in_g']:.1f} g", "Feedstock", "flame")
        with c:
            metric_card("Elapsed", fmt_duration(elapsed), "Since logging started", "ember")
        st.write("")
        mass_out = st.number_input(
            "Final biochar mass (g)", min_value=0.0, max_value=100000.0, value=0.0, step=1.0,
            help="Leave at 0 if you have not weighed the biochar yet.")
        if st.button("Stop and save session", type="primary"):
            stop_session(current["id"], mass_out)
            st.rerun()

    st.divider()
    st.subheader("Previous sessions")
    raw = pd.DataFrame(all_sessions())
    if raw.empty:
        st.info("No sessions yet. Start one above and it will appear here.")
        return
    st.dataframe(sessions_view(raw.copy()), width="stretch", hide_index=True, column_config={
        "Mass in (g)": st.column_config.NumberColumn(format="%.1f"),
        "Biochar out (g)": st.column_config.NumberColumn(format="%.1f"),
        "Yield (%)": st.column_config.NumberColumn(format="%.1f"),
        "Duration (min)": st.column_config.NumberColumn(format="%.1f"),
        "Peak (°C)": st.column_config.NumberColumn(format="%.1f"),
        "Minutes in band": st.column_config.NumberColumn(format="%.1f"),
    })


# ----------------------------------------------------------- history/export
def page_history() -> None:
    st.subheader("Data history")
    raw = pd.DataFrame(recent_readings(5000))
    if raw.empty:
        st.info("No telemetry yet. Open the Dashboard to generate demo readings.")
    else:
        view = raw.copy()
        view["created_at"] = localize(view["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"Showing the latest {len(view):,} readings, newest first "
                   "(local time). The CSV keeps UTC timestamps.")
        st.dataframe(view.iloc[::-1], width="stretch", hide_index=True)
        st.download_button("⬇  Download telemetry CSV",
                           raw.to_csv(index=False).encode("utf-8"),
                           file_name="blaze_telemetry_demo.csv", mime="text/csv")

    st.divider()
    st.subheader("Session export")
    sessions = pd.DataFrame(all_sessions(1000))
    if sessions.empty:
        st.info("No sessions to export yet.")
    else:
        st.download_button("⬇  Download session log CSV",
                           sessions.to_csv(index=False).encode("utf-8"),
                           file_name="blaze_session_log.csv", mime="text/csv")


# ----------------------------------------------------------------- settings
def page_settings() -> None:
    st.subheader("Display settings")
    st.caption("These settings affect only this dashboard, not any device.")
    ss.chart_points = st.slider("Chart history (recent samples)", 20, 500,
                                int(ss.chart_points), 10)
    c1, c2 = st.columns(2)
    c1.number_input("Reference band, lower edge (°C)", value=int(BAND_LOW), disabled=True)
    c2.number_input("Reference band, upper edge (°C)", value=int(BAND_HIGH), disabled=True)
    st.caption("Band edges are fixed in database.py and used for display and session statistics.")

    st.divider()
    st.subheader("Demo data")
    confirm = st.checkbox("I want to delete all stored demo telemetry")
    if st.button("Clear telemetry", disabled=not confirm):
        clear_telemetry()
        ss.last_alert = ""
        st.success("Telemetry cleared. Session records were kept.")

    st.warning(
        "This app has no remote configuration, valve command, or burner control. "
        "Keep every real safety function independent of the dashboard, and have "
        "qualified people review any gas or high-temperature equipment.")


# -------------------------------------------------------------------- about
def page_about() -> None:
    st.subheader("About this prototype")
    st.markdown("""
**Included**
- Live temperature cards, a thermal-zone strip, and a time-series chart
- Shaded 300–500 °C reference band
- Simulated heating, hold and shutoff states, with the simulated valve following them
- Simulated sensor fault: no valid reading, valve fails closed
- Batch records with feedstock mass, biochar mass and yield
- CSV export for telemetry and sessions

**Not included**
- Real thermocouple or ESP32 connection
- WebSocket ingestion
- Valve, servo, relay, burner or heater control
- Safety interlocks, watchdogs or emergency shutoff

This is a software demonstration and research-recording tool, not an
industrial controller or a safety-rated monitor.
""")


{
    "Dashboard": page_dashboard,
    "Session logging": page_sessions,
    "History & export": page_history,
    "Settings": page_settings,
    "About": page_about,
}[page]()
