# BLAZE Python Dashboard (simulation-only)
A beginner-friendly Streamlit dashboard for the BLAZE research project.

## Safety boundary
This project is deliberately a **simulation and research-logging prototype**.
It does not connect to a real thermocouple, ESP32, LPG valve, burner, servo,
relay, heater, or kiln. It cannot command physical equipment.

The shaded 300–500°C region is a research display reference only. It is not
an operating target, a recommended process setting, or a safety limit.
Do not use this dashboard as a safety system.

## 1. Install tools
1. Install Python 3.11 or newer from https://www.python.org/downloads/
2. Install Visual Studio Code.
3. In VS Code, install the Microsoft Python extension.
4. Open this `BLAZE_Python_Dashboard` folder.

## 2. Create a virtual environment

Open **Terminal > New Terminal** in VS Code.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Run the dashboard

```bash
streamlit run app.py
```

Streamlit will print a local address, usually:

`http://localhost:8501`

Open that address in your browser.

## 5. Try the features

- Dashboard: run/pause the synthetic data simulator and view the chart.
- Click **Simulate sensor fault** to test the in-app warning.
- Session logging: create a research batch record and enter measured masses.
- History & export: download telemetry and session records as CSV.
- Settings: see the display-only reference settings.

## 6. Reset the demo database

Stop Streamlit with `Ctrl+C`. Then delete:

`data/blaze.db`

The database will be recreated automatically the next time the app starts.

## Troubleshooting

- `streamlit is not recognized`: activate `.venv` and run `python -m pip install -r requirements.txt`.
- `No module named plotly`: run `pip install plotly`.
- Port already in use: run `streamlit run app.py --server.port 8502`.
- Database locked: close duplicate dashboard processes and restart Streamlit.

## Suggested safe development milestones

1. Confirm the simulator dashboard works.
2. Test session logging and CSV exports using sample data.
3. Add data-quality checks and a clear simulated/live data label.
4. If real sensors are later studied, keep initial work to supervised, low-voltage,
   disconnected bench testing and read-only data display. Any actual thermal or
   gas equipment must remain outside this app and be handled under qualified
   professional safety engineering.
