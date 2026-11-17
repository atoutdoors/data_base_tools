# Database Tools

Utilities for adding float deployments and processing incoming BGC float logs into the WHOI database.

The main workflows are:

1. Add a new NAVIS or SOLO deployment.
2. Parse an incoming log, load calibration data, and update deployment and sensor records.

## Repository layout

```text
argo-db-tools/
|-- read_incoming_log.py
|-- run_read_incoming_log.bat
|-- add_default_Navis_deployment.py
|-- add_default_SOLO_deployment.py
|-- add_deployment.py
|-- bgc_database.py
|-- requirements.txt
`-- README_read_incoming_log.md
```

See [`argo-db-tools/README_read_incoming_log.md`](argo-db-tools/README_read_incoming_log.md) for the complete incoming-log guide.

## Setup

Windows and Python 3 are recommended.

1. Copy `argo-db-tools/.env.example` to `argo-db-tools/.env`.
2. Add the database token to `.env`:

   ```text
   TOKEN=Token YOUR_DATABASE_TOKEN_HERE
   ```

3. Keep `.env` private. It is ignored by Git and must not be committed or pushed.

The batch launcher creates a local virtual environment and installs the packages in `requirements.txt` on first use.

## Processing incoming logs

Edit the path variables near the top of `argo-db-tools/read_incoming_log.py`:

```python
checklog = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\checkout\incoming.log"
sunacal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\SUNA\SUNA.cal"
phcal = r"C:\calibration\pH\22230-20555 Float Calsheet.pdf"
ocrcal = r"C:\calibration\OCR.cal"
opticscal = r"C:\calibration\MCOMSC-0540_CharSheets.pdf"
```

For SOLO floats, also set `ctdcal` and `o2cal`.

Run the parser with:

```powershell
cd "C:\path\to\data_base_tools\argo-db-tools"
.\run_read_incoming_log.bat
```

Database updates are enabled by default. To inspect the parsed results without writing to the database:

```powershell
.\run_read_incoming_log.bat --no-db
```

The parser supports NAVIS, NAVIS-83, and SOLO formats. It can read calibration values from incoming logs, `.cal` files, selectable-text PDFs, OCR-504 files, and shared MCOMSC characterization sheets. It updates or creates:

- Deployment metadata
- CTD temperature, conductivity, and pressure sensors
- Oxygen and pH sensors
- SUNA nitrate sensor
- OCR sensor
- CDOM/FDOM, CHLA, and BBP sensors

If a calibration path is blank, the parser prompts for it. CDOM, CHLA, and BBP use one shared optics PDF path.

## Adding a deployment

### NAVIS deployment

Open `add_default_Navis_deployment.py` and change at least:

```python
FLOAT_SERIAL_NO = 2018
```

Review `PLATFORM_TYPE` and the other deployment metadata, then run:

```powershell
cd "C:\path\to\data_base_tools\argo-db-tools"
.venv\Scripts\python.exe add_default_Navis_deployment.py
```

The template uses `NAVIS_EBR` and initializes empty `missions` and `sensors` lists.

### SOLO deployment

Open `add_default_SOLO_deployment.py` and change:

```python
FLOAT_SERIAL_NO = 4057
```

Review the metadata, then run:

```powershell
.venv\Scripts\python.exe add_default_SOLO_deployment.py
```

The template uses `SOLO_BGC_MRV` and also initializes empty `missions` and `sensors` lists.

### Custom deployment

Use `add_deployment.py` when the default NAVIS or SOLO templates do not contain the required metadata. Edit its `data` dictionary before running it. The script sends the complete deployment payload through `post_deployment`.

Do not run an add-deployment script repeatedly for the same float unless the API or database administrator confirms that duplicate creation is safe.

## Recommended workflow

1. Create the deployment with the appropriate default or custom deployment script.
2. Confirm the deployment exists in the database.
3. Configure the incoming-log and calibration paths.
4. Run `run_read_incoming_log.bat`.
5. Review the printed sensor dates, coefficient status, and `updated`/`added` messages.

The incoming-log script also attempts to create a missing deployment automatically, but creating it explicitly first provides better control over platform metadata.

## Database behavior

`bgc_database.py` reads `.env` from the same folder as the module, so the tools can be launched from any current directory. Deployment updates use the database API; if the deployment is missing, the incoming-log workflow attempts to create it. Sensor records are updated individually, with an add fallback when no existing sensor record is found.

Common errors:

- `401`: missing or invalid `TOKEN` in `.env`.
- `400`: invalid or incomplete deployment/sensor payload.
- `404`: deployment or sensor does not exist; the script attempts an add where supported.
- `No module named ...`: run the batch launcher so its local environment installs dependencies.
- No PDF coefficients: the PDF is likely image-only or uses a different label layout. Use an OCR-readable PDF and review the parser output.

Never place the real database token in Python source, README files, batch files, or GitHub commits.
