# Running `read_incoming_log`

`read_incoming_log.py` parses NAVIS, NAVIS-83, and SOLO incoming logs, reads available calibration files, and updates the database.

## First-time setup

1. Install Python 3 on the Windows computer.
2. Copy `.env.example` to `.env` in this folder.
3. Open `.env` and add the database token:

   ```text
   TOKEN=Token YOUR_DATABASE_TOKEN_HERE
   ```

   Keep `.env` private. It is excluded from GitHub.

## Configure file paths

Open `read_incoming_log.py` and edit the path variables near the top:

```python
checklog = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\checkout\incoming.log"
sunacal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\SUNA\SUNA.cal"

# Used for SOLO floats:
ctdcal = r""
phcal = r""
o2cal = r""

# Optional OCR and shared CDOM/CHLA/BBP calibration files:
ocrcal = r""
opticscal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\MCOMSC\MCOMSC-0540_CharSheets.pdf"
```

The CDOM, CHLA, and BBP values should use one shared characterization-sheet PDF in `opticscal`.

Use raw Python strings for Windows paths. The leading `r` prevents backslashes such as `\n` from being interpreted as escape characters.

## What each input provides

| Input | Used for |
| --- | --- |
| Incoming checklog | Float serial number, platform metadata, battery voltage when present, CTD coefficients, oxygen coefficients, and inline SUNA information |
| `sunacal` | Nitrate/SUNA coefficients, SUNA serial number, and calibration date |
| `phcal` | pH serial number, K0 calibration date, K0/K2/f(P) coefficients |
| `ctdcal` | SOLO CTD temperature, conductivity, and pressure coefficients |
| `o2cal` | SOLO SBE83 oxygen serial number, date, and coefficients |
| `ocrcal` | OCR-504 wavelength-specific coefficients |
| `opticscal` | BBP dark counts/scale factor, CHLA dark counts/scale factor, and FDOM/CDOM dark counts/scale factor |

The shared MCOMSC characterization sheet is read page by page so values from BBP, CHLA, and FDOM pages do not get mixed together.

## NAVIS example

For NAVIS or NAVIS-83, set at least the incoming log and SUNA file:

```python
checklog = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\checkout\F1753_incoming.log"
sunacal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\SUNA\SNA0000A.cal"
phcal = r"C:\calibration\22230-20555 Float Calsheet.pdf"
ocrcal = r"C:\calibration\OCR.cal"
opticscal = r"C:\calibration\MCOMSC-0540_CharSheets.pdf"
```

The checklog is parsed first. If pH, OCR, SUNA, or optics paths are blank, the script asks for them interactively.

## SOLO example

SOLO logs require separate CTD, pH, and oxygen calibration files in addition to SUNA:

```python
checklog = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\checkout\4057_full_bit.log"
sunacal = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\sensor_cal\SUNA\SUNA_2476.cal"
ctdcal = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\sensor_cal\CTD_DOXY\21464.cal"
phcal = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\sensor_cal\pH\22230-20555 Float Calsheet.pdf"
o2cal = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\sensor_cal\SBE83\0238.cal"
opticscal = r"G:\Shared drives\WHOI Argo\BGC\Floats\4057\sensor_cal\MCOMSC\MCOMSC-0540_CharSheets.pdf"
```

If any required SOLO path is missing, the script keeps asking until a valid file path is supplied.

## Run the batch file

From PowerShell, run:

```powershell
cd "C:\path\to\argo-db-tools"
.\run_read_incoming_log.bat
```

The batch file creates a local `.venv` and installs the required packages on the first run. It works even when launched from another current directory.

Database updates are enabled by default. To parse without writing to the database:

```powershell
.\run_read_incoming_log.bat --no-db
```

Use `--no-prompt` only when every required path is already configured:

```powershell
.\run_read_incoming_log.bat --no-prompt
```

## Missing calibration paths

If a path is blank or does not exist, the script prompts for it. For a NAVIS float, it may ask for:

- SUNA calibration file
- pH calibration file or PDF
- OCR calibration file
- One shared CDOM/CHLA/BBP calibration PDF

For a SOLO float, it also asks for the CTD and oxygen calibration files.

Press Enter to skip an optional calibration file. Required SOLO calibration files cannot be skipped.

## Calibration formats

- pH calibration sheets: selectable-text PDF or compatible calibration text file.
- MCOMSC optics characterization sheets: the parser extracts BBP, CHLA, and FDOM/CDOM values from the characterization pages.
- SUNA calibration files: `.cal` files are used for nitrate coefficients, serial number, and calibration date.
- OCR calibration files: the OCR-504 wavelength table format is supported.

Scanned image-only PDFs must be converted to an OCR-readable PDF before running the script.

## Output and database behavior

The script prints each sensor, whether coefficients were found, its calibration date, and whether the record was updated or added. If a deployment is not already in the database, the script attempts to create it before submitting the sensor records.

If the database call fails, the HTTP status and response are printed. Common causes are an absent or invalid `.env` token, no network access, or a deployment that the API rejects.

## Direct Python usage

The batch file is recommended because it manages dependencies. Once the environment is installed, the script can also be run directly:

```powershell
.venv\Scripts\python.exe read_incoming_log.py
```

Use `--help` to see the available command-line options.

Available options include:

```text
--no-db       Parse and display results without changing the database.
--no-prompt   Do not ask for missing paths; fail instead.
--add-to-db   Explicitly request database updating (database updating is already the default).
--ctd-cal     Override the configured SOLO CTD calibration path.
--ph-cal      Override the configured pH calibration path.
--o2-cal      Override the configured SOLO oxygen calibration path.
--ocr-cal     Override the OCR calibration path.
--optics-cal  Override the shared CDOM/CHLA/BBP PDF path.
```

## Reading the output

Typical output looks like:

```text
Parsed float 1753 (NAVIS_EBR)
  CTD_TEMP: calibration found; date=2026-08-12
  TRANSISTOR_PH: calibration found; date=2026-08-12
  FLUOROMETER_CDOM: calibration found; date=2026-10-13
  FLUOROMETER_CHLA: calibration found; date=2026-10-13
  BACKSCATTERINGMETER_BBP700: calibration found; date=2026-10-13
TRANSISTOR_PH: updated
FLUOROMETER_CDOM: added
```

`updated` means the API found an existing sensor record. `added` means the update failed and the script attempted to create a new sensor record. A deployment that does not exist is also created automatically with empty `missions` and `sensors` lists; sensor records are submitted separately.

## Troubleshooting

### `No module named requests`, `pandas`, or `pypdf`

Run `run_read_incoming_log.bat` instead of launching the script with a different Python interpreter. The batch file creates `.venv` and installs `requirements.txt`.

### The database token is missing

Confirm that the file is named exactly `.env` and is beside `bgc_database.py`. It must contain a valid `TOKEN=` line. Do not commit or email this file.

### A PDF has no calibration values

The PDF must contain selectable text. Image-only scans need OCR before they can be parsed. If the PDF has a different label layout, run once with `--no-db`, review the printed sensor output, and provide the calibration sheet for parser-specific mapping.

### The deployment update fails

Read the HTTP status and response printed by the script. A `401` usually means the token is invalid or missing; a `404` may mean the deployment was not registered, in which case the script attempts to create it; a `400` usually indicates a field or payload validation problem.
