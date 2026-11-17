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
