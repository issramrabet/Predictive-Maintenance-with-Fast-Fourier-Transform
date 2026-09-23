# Vibration Signature Analysis — Predictive Maintenance

> 🎥 Demo video: [add your LinkedIn/YouTube link here]

Predictive maintenance application for an asynchronous motor, built around a
**Hansford HS-173HT** triaxial accelerometer + temperature sensor. It computes
a live H-FFT, interprets peaks against a defect catalog (unbalance,
misalignment, mechanical looseness, bearing defects BPFO/BPFI/BSF/FTF,
electrical faults, broken rotor bars, gear defects, cavitation, loose
feet/flange), and applies **ISO 20816-3** severity thresholds.

No hardware is required to use it: the backend ships a physics-based
simulator that generates realistic defect signatures, with a single swap
point to plug in a real sensor later (see
[Moving to a real sensor](#moving-to-a-real-sensor)).

## Architecture overview

```
┌─────────────────────┐        WebSocket (live)        ┌──────────────────────┐
│                      │ ───────────────────────────▶   │                      │
│   React Frontend     │        REST (config/history)   │   FastAPI Backend    │
│   Custom dark UI      │ ◀───────────────────────────▶  │   + physics engine   │
│                      │                                 │   + SQLite           │
└─────────────────────┘                                 └──────────────────────┘
```

- **Backend** (`/backend`) — FastAPI + NumPy. Simulates the sensor signal,
  computes a windowed FFT, derives RMS velocity (ISO 20816), crest factor,
  kurtosis, peak acceleration, and a formula-based health score; persists
  history to SQLite; streams every analyzed frame over WebSocket.
- **Frontend** (`/frontend`) — React + Vite with a custom-built dark UI (no
  component-library dependency): a sidebar-nav shell, gradient-accented
  cards, and Recharts-based gradient area/line/donut charts. Four pages:
  Dashboard, H-FFT
  Analysis, History, Motor Configuration.

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # adjust if needed
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`, interactive docs at
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env               # adjust VITE_API_URL if the backend is elsewhere
npm run dev
```

Open `http://localhost:5173`.

## Pages

### Dashboard (`/`)
Dense, widget-grid layout (health score gauge, overall status, per-axis RMS,
temperature, crest factor, kurtosis, peak acceleration, RMS trend with ISO
20816 thresholds overlaid, severity distribution donut, thermal trend, alert
log) plus a **demo mode** dropdown to inject any catalog fault without a
physical sensor.

### H-FFT Analysis (`/fft`)
Live spectrum on the X axis with catalogued peaks overlaid, raw time-domain
waveform of the latest window, and an interpretation table (frequency,
measured amplitude, thresholds, status) — click a row to see the peak detail.

### History (`/history`)
Time-range filter (15 min / 1 hour / 24 hours / all), RMS and thermal trend
charts over the selected range, health score and kurtosis trend charts, a
paginated snapshot table, and the full alert log.

### Motor Configuration (`/config`)
Full form: rotation speed (N ↔ f_r synced), bearing geometry (n, Db, De, Di,
φ), IEC 60034-7 mounting mode (with the associated defect family — feet or
flange), machine-specific parameters (mains frequency, slip, gear teeth,
pump vanes), and power/foundation for ISO 20816-3 threshold calculation.
Any change recalculates defect frequencies and amplitude thresholds
immediately on the backend.

## Diagnostic metrics

| Metric | What it flags | Notes |
|---|---|---|
| RMS velocity (mm/s) | Overall vibration severity | ISO 20816-3 zones B/C/C-D |
| Crest factor (peak/RMS) | Early impulsive bearing faults | Healthy ≈ 1.4 (√2) |
| Kurtosis | Early impulsive bearing faults | Healthy ≈ 3.0; impacts push it higher |
| Health score (0-100) | Composite severity index | **Formula-based**, derived directly from the ISO 20816 thresholds already in force — not a trained model |

Note the BPFI/BPFO/BSF injection scenarios in demo mode: crest factor and
kurtosis spike well before RMS velocity does, which is exactly why they're
tracked separately — the health score (RMS-based) can stay high even while
those two are flagging a developing fault. That gap is real physics, not a
bug: it's the argument for the RUL work below.

## Roadmap: Remaining Useful Life

There's a "Remaining Useful Life" card on the dashboard that's intentionally
left as a placeholder rather than showing a fabricated number. A real RUL
estimate needs a trained model — this is a legitimate follow-on project, not
a small addition. Good starting points:

- **Datasets**: [MAFAULDA](http://www02.smt.ufrj.br/~offshore/mfs/page_01.html),
  [NASA/IMS Bearing Dataset](https://www.kaggle.com/vinayak123tyagi/bearing-dataset),
  see also [Charlie5DH/PredictiveMaintenance-and-Vibration-Resources](https://github.com/Charlie5DH/PredictiveMaintenance-and-Vibration-Resources)
  for a broader list of datasets and papers.
- **Approach**: extract features per window (RMS, crest factor, kurtosis,
  peak amplitudes per defect frequency — all of which this backend already
  computes) → train a regression or survival model on run-to-failure data →
  serve predictions from a new endpoint (e.g. `/api/status/rul`) → add a
  `RulGauge` widget alongside `HealthGauge` on the dashboard.
- This backend's `fft_engine.py` already extracts most of the standard
  feature set used in the vibration-analysis literature, so the plumbing to
  add a feature-extraction pipeline for training data is mostly already
  there.

## API reference

All `/api/*` routes accept an `X-API-Key` header — disabled by default for
local dev (`VIBRO_REQUIRE_API_KEY=false` in `.env`). Enable it and set a
real secret before exposing this beyond `localhost`.

| Method | Route | Description |
|---|---|---|
| GET | `/api/health` | Liveness, no auth required |
| GET/PUT | `/api/config` | Read/update machine configuration |
| GET | `/api/config/fixation-codes` | IEC 60034-7 mounting code table |
| GET | `/api/config/defect-frequencies` | Computed frequencies/thresholds for the current config |
| GET | `/api/status` | One-shot current reading (HTTP fallback) |
| WS | `/api/realtime/ws` | Live feed — one analyzed frame per tick |
| POST | `/api/realtime/demo-fault` | Inject a simulated fault (`{"fault": "5"}` or `null`) |
| GET | `/api/realtime/fault-options` | Available faults for injection |
| GET | `/api/history/snapshots` | Persisted history (RMS, temperature, health score, severity) |
| GET | `/api/history/severity-summary` | Counts per severity bucket (feeds the donut chart) |
| GET | `/api/history/alerts` | Severity transition log |

## Moving to a real sensor

The HS-173HT is an analog accelerometer (100 mV/g × 3 axes + 10 mV/°C) — it
needs a DAQ/ADC to be digitized. The swap point is
`backend/app/simulator.py`: implement `SensorSource.read_frame()` to read
your real samples (e.g. via a National Instruments DAQ, a Modbus module, or
a serial read), keeping the same `SensorFrame` structure (X/Y/Z axes in
mm/s² + temperature in °C). Nothing else — FFT, thresholds, persistence,
API, frontend — needs to change.

```python
class RealDaqSensorSource(SensorSource):
    def read_frame(self, cfg: MachineConfig) -> SensorFrame:
        # read N_SAMPLES samples per axis at SAMPLE_RATE_HZ from your DAQ
        ...
```

Then in `backend/app/tasks.py`, replace `sensor_source = SimulatedSensorSource()`
with your implementation.

## Calibration notes

The simulator generates physically plausible signals (waveform shapes,
harmonics, slip-modulated bearing impacts) but its **amplitude scale is not
calibrated against a real sensor** — it was chosen to stay readable on the
chart. Once a real HS-173HT is wired up, adjust `base_scale` in
`simulator.py` (or calibrate at the DAQ level) so the ISO 20816 thresholds
(mm/s RMS, derived from the power/foundation table) reflect real
measurements on your machine.

## Project structure

```
backend/
  app/
    physics.py        # defect frequency formulas, ISO 20816 thresholds, health score formula
    simulator.py       # simulated sensor source (hardware swap point)
    fft_engine.py        # windowed FFT, RMS velocity, crest factor, kurtosis, peak matching
    tasks.py              # acquisition loop: simulate → analyze → persist → broadcast
    models.py / database.py   # SQLAlchemy / SQLite
    routers/             # config, realtime (WS), history, status
    main.py               # FastAPI application
  requirements.txt
  .env.example
frontend/
  src/
    api/                # REST client + WebSocket hook
    context/             # shared machine configuration
    components/           # Card, StatCard, Badge, gradient charts, gauge, donut, table
    pages/                 # Dashboard, FFTAnalysis, History, MachineConfig
    App.jsx                 # Sidebar shell + routing
  package.json
  .env.example
```

## Troubleshooting

**`pip install` fails trying to build `ninja` (or `numpy`) from source.**
This means pip couldn't find a prebuilt wheel for the pinned package version
on your Python version/OS/architecture, so it fell back to compiling it —
which needs a C/C++ toolchain most machines don't have set up. Two fixes,
in order of preference:
1. `pip install --upgrade pip` first, then retry — older pip versions are
   worse at picking the right wheel.
2. If it's `numpy` specifically: `requirements.txt` pins a range
   (`numpy>=1.26,<3`), not an exact version, so pip should already be free
   to pick whichever release has a wheel for you. If you still hit this,
   check `python --version` — Python versions older than 3.9 or newer than
   the numpy release cycle supports can lack wheels entirely.

## Security before production

- Enable `VIBRO_REQUIRE_API_KEY=true` and set a long, random secret in `.env`.
- Restrict `VIBRO_CORS_ORIGINS` to your actual frontend domain.
- Move from SQLite to Postgres (`VIBRO_DATABASE_URL`) for a multi-instance
  deployment.
- The WebSocket (`/api/realtime/ws`) is not authenticated in this version —
  put it behind your reverse proxy / auth layer before any public exposure.

## License

MIT — see [LICENSE](LICENSE).

