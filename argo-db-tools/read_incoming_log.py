"""Parse NAVIS and SOLO incoming/calibration logs."""

from datetime import datetime, timedelta
import argparse
from pathlib import Path
import re

import bgc_database as db
from decode_suna_cal import decode_suna_cal

# Edit these paths to run the script directly from your IDE.
checklog = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\checkout\F1753_incoming_20261105.log"
sunacal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\SUNA\SNA2468A.cal"
ctdcal = r""
phcal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\pH\22230-20555 Float Calsheet.pdf"
o2cal = r""
ocrcal = r""
opticscal = r"G:\Shared drives\WHOI Argo\BGC\Floats\1753\sensor_cal\MCOMSC\MCOMSC-0540_CharSheets.pdf"


def _read_pdf_pages(path):
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("PDF support requires pypdf; run the batch file once to install it") from error
    pages = [page.extract_text() or "" for page in PdfReader(str(path)).pages]
    if not any(page.strip() for page in pages):
        raise ValueError(f"No selectable text found in PDF: {path}. An OCR-readable PDF is required.")
    return pages


def _read_pages(path):
    if Path(path).suffix.lower() == ".pdf":
        return _read_pdf_pages(path)
    return ["\n".join(_read_lines(path))]


def _read_lines(path):
    """Read legacy instrument files across Windows and Python versions."""
    if Path(path).suffix.lower() == ".pdf":
        return "\n".join(_read_pdf_pages(path)).splitlines()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as stream:
                return stream.readlines()
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Could not decode {path}")


def _value(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _labeled_digits(line, label):
    """Return the digit value following a NAVIS label.

    NAVIS checklogs have used several separators over time (``:``, ``=``
    and bracketed values), and some versions insert spaces into ICCIDs.
    Keep the label-specific match narrow so an unrelated number on the same
    diagnostic line is not mistaken for the modem identifier.
    """
    match = re.search(
        rf"{label}(?:[\s:=\[])*([0-9][0-9\s-]*[0-9]|[0-9])",
        line,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = re.sub(r"[\s-]", "", match.group(1))
    return value or None


def _date(value):
    value = str(value).strip().strip('"').rstrip(",;")
    iso_date = re.search(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)", value)
    if iso_date:
        return iso_date.group(1)
    text_date = re.search(r"\b(\d{1,2}-[A-Za-z]{3}-\d{2,4})\b", value)
    if text_date:
        value = text_date.group(1)
    slash_date = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", value)
    if slash_date:
        value = slash_date.group(1)
    for fmt in (
        "%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y",
        "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
    ):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            pass
    return value


def _sensor(name, maker=None, model=None, coefficients=None, **extra):
    sensor = {
        "SENSOR": name,
        "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
        "PREDEPLOYMENT_CALIB_COEFFICIENT": coefficients,
        "ADD_DATE": datetime.now().isoformat(),
    }
    if maker:
        sensor["SENSOR_MAKER"] = maker
    if model:
        sensor["SENSOR_MODEL"] = model
    sensor.update(extra)
    return sensor


def _base_sensors(mcoms_model="MCOMS_FLBBCD"):
    return {
        "temp": _sensor("CTD_TEMP", "SBE"),
        "cndc": _sensor("CTD_CNDC", "SBE"),
        "pres": _sensor("CTD_PRES", "DRUCK", "DRUCK_2900PSIA"),
        "doxy": _sensor("OPTODE_DOXY", "SBE"),
        "ph": _sensor("TRANSISTOR_PH", "SBE", "SEAFET", {
            key: None for key in ("F0", "F1", "F2", "F3", "F4", "F5", "F6", "K0", "K2")
        }),
        "cdom": _sensor("FLUOROMETER_CDOM", "WETLABS", mcoms_model,
                         {"DARK_CDOM": None, "SCALE_CDOM": None}),
        "chla": _sensor("FLUOROMETER_CHLA", "WETLABS", mcoms_model,
                         {"DARK_CHLA": None, "SCALE_CHLA": None}),
        "bbp": _sensor("BACKSCATTERINGMETER_BBP700", "WETLABS", mcoms_model,
                        {"KHI": 1.097, "BETASW700": "calculated at 124 angularDeg",
                         "DARK_BACKSCATTERING700": None, "SCALE_BACKSCATTERING700": None}),
        "nitrate": _sensor("SPECTROPHOTOMETER_NITRATE", "SATLANTIC", "SUNA_V2",
                            {"calibration file": None}),
    }


def _parse_ph_cal(path, sensor):
    """Parse the Sea-Bird Scientific ISFET pH calibration format."""
    coefficients = {}
    text = " ".join(_read_lines(path))
    match = re.search(
        r'FET[-_ ]*REF[_ ]*serial[_ ]*number\s*(?:=|:)\s*"?([\d-]+)',
        text,
        re.I,
    )
    if not match:
        match = re.search(
            r'(?:serial_number|ISFET[_ ]*serial[_ ]*number|serial\s*no\.?)\s*(?:=|:)\s*"?([\d-]+)',
            text,
            re.I,
        )
    if match:
        sensor["SENSOR_SERIAL_NO"] = match.group(1)
    date_value = r'((?:\d{4}-\d{2}-\d{2})|(?:\d{1,2}[-/]\w+[-/]\d{2,4})|(?:\d{1,2}/\d{1,2}/\d{2,4})|(?:[A-Za-z]+\s+\d{1,2},?\s+\d{4}))'
    date_labels = (
        r"K0[_ ]*calibration[_ ]*date",
        r"calibration[_ ]*date",
        r"Calsheet[_ ]*Creation[_ ]*Date",
        r"\bdate\b",
    )
    match = None
    for label in date_labels:
        match = re.search(rf'{label}\s*(?:=|:)\s*"?{date_value}', text, re.I)
        if match:
            break
    if match:
        sensor["SENSOR_CALIB_DATE"] = _date(match.group(1))
    if not sensor.get("SENSOR_CALIB_DATE"):
        any_date = re.search(
            r"(?<!\d)(\d{4}-\d{2}-\d{2}|\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}|\d{1,2}/\d{1,2}/\d{2,4})(?!\d)",
            text,
            re.I,
        )
        if any_date:
            sensor["SENSOR_CALIB_DATE"] = _date(any_date.group(1))
    number = r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
    for match in re.finditer(rf"\b(f\d+|K0|K2f\d+)\s*=\s*{number}", text, re.I):
        key = match.group(1)
        key = key[0].upper() + key[1:] if key.lower().startswith("f") else key
        coefficients[key] = _number(match.group(2))
    sensor["PREDEPLOYMENT_CALIB_COEFFICIENT"] = coefficients


def _parse_suna_metadata(path, sensor):
    """Extract SUNA serial number and calibration-file creation date."""
    text = " ".join(_read_lines(path))
    match = re.search(r"SUNA\s+(\d+)\s+Cal", text, re.I)
    if not match:
        match = re.search(r"SNA(\d+)[A-Z]?\b", str(path), re.I)
    if match:
        sensor["SENSOR_SERIAL_NO"] = match.group(1)
    dates = re.findall(r"File creation time\s+(\d{1,2}-[A-Za-z]{3}-\d{4})", text, re.I)
    if dates:
        sensor["SENSOR_CALIB_DATE"] = _date(dates[-1])


def _parse_ocr_cal(path, sensor):
    """Parse the OCR-504 calibration notebook's wavelength table."""
    numeric_rows = []
    number_pattern = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    for line in _read_lines(path):
        values = re.findall(number_pattern, line)
        if values:
            numeric_rows.append([float(value) for value in values])
    if len(numeric_rows) < 11:
        raise ValueError(f"OCR calibration file has too few numeric rows: {path}")

    coefficients = {}
    for wavelength_row, coefficient_row in zip((3, 5, 7, 9), (4, 6, 8, 10)):
        wavelength = int(round(numeric_rows[wavelength_row][0]))
        values = numeric_rows[coefficient_row]
        if len(values) < 3:
            raise ValueError(f"OCR calibration row is incomplete: {path}")
        coefficients[f"{wavelength} A0"] = values[0]
        coefficients[f"{wavelength} A1"] = values[1]
        coefficients[f"{wavelength} im"] = values[2]
    sensor["PREDEPLOYMENT_CALIB_COEFFICIENT"] = coefficients


def _parse_optical_cal(path, sensor, sensor_name):
    """Parse labeled CDOM, CHLA, or BBP coefficients from a text/PDF file."""
    aliases = {
        "cdom": {
            "DARK_CDOM": r"(?:(?:DARK|OFFSET)[^0-9:=]{0,30}(?:CDOM|FDOM)|(?:CDOM|FDOM)[^0-9:=]{0,30}(?:DARK|OFFSET))",
            "SCALE_CDOM": r"(?:(?:SCALE|SLOPE|SENSITIVITY)[^0-9:=]{0,30}(?:CDOM|FDOM)|(?:CDOM|FDOM)[^0-9:=]{0,30}(?:SCALE|SLOPE|SENSITIVITY))",
        },
        "chla": {
            "DARK_CHLA": r"(?:DARK[_ ]*CHLA|CHLA[_ ]*DARK)",
            "SCALE_CHLA": r"(?:SCALE[_ ]*CHLA|CHLA[_ ]*SCALE)",
        },
        "bbp": {
            "DARK_BACKSCATTERING700": r"(?:DARK[_ ]*(?:BACKSCATTERING[_ ]*700|BBP[_ ]*700)|BBP[_ ]*700[_ ]*DARK)",
            "SCALE_BACKSCATTERING700": r"(?:SCALE[_ ]*(?:BACKSCATTERING[_ ]*700|BBP[_ ]*700)|BBP[_ ]*700[_ ]*SCALE)",
            "KHI": r"KHI",
            "BETASW700": r"BETA[_ ]*SW[_ ]*700",
        },
    }
    coefficients = dict(sensor.get("PREDEPLOYMENT_CALIB_COEFFICIENT") or {})
    number = r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
    label_suffix = r"(?:[\s_()\-]+(?:COUNTS?|FACTOR|COEFFICIENTS?|VALUE))*[\s_()\-]*"
    found = False
    lines = _read_lines(path)

    # Sea-Bird MCOMSC characterization sheets place the numeric value before
    # the explanatory label.  For example: ``50 counts`` followed by
    # ``Dark counts Range ...`` and then the scale factor on the next line.
    sheet_text = "\n".join(lines)
    if "Characterization Sheet" in sheet_text and sensor_name in ("cdom", "chla", "bbp"):
        pages = _read_pages(path)
        page_markers = {
            "bbp": ("Wavelength:", "BBP(l)"),
            "chla": ("Chlorophyll Fluorometer Characterization Sheet",),
            "cdom": ("FDOM Fluorometer Characterization Sheet",),
        }
        block = next(
            (page for page in pages if any(marker in page for marker in page_markers[sensor_name])),
            sheet_text,
        )
        dark = re.search(rf"{number}\s+counts?\s*\n\s*Dark counts?", block, re.I)
        scale = re.search(rf"Dark counts[^\n]*\n\s*{number}", block, re.I)
        if dark:
            key = {
                "cdom": "DARK_CDOM",
                "chla": "DARK_CHLA",
                "bbp": "DARK_BACKSCATTERING700",
            }[sensor_name]
            coefficients[key] = _number(dark.group(1))
            found = True
        if scale:
            key = {
                "cdom": "SCALE_CDOM",
                "chla": "SCALE_CHLA",
                "bbp": "SCALE_BACKSCATTERING700",
            }[sensor_name]
            coefficients[key] = _number(scale.group(1))
            found = True
        if sensor_name == "bbp":
            chi = re.search(
                r"(\d+(?:\.\d+)?)\s+sr(?!\s*[-\d]).{0,300}?Centroid Angle.*?Chi factor\s*c",
                block,
                re.I | re.S,
            )
            if chi:
                coefficients["KHI"] = _number(chi.group(1))
        serial = re.search(r"\b(MCOMSC-\d+)\b", block, re.I)
        if serial:
            sensor["SENSOR_SERIAL_NO"] = serial.group(1)
        date = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", block)
        if date:
            sensor["SENSOR_CALIB_DATE"] = datetime.strptime(
                date.group(1), "%m/%d/%Y"
            ).strftime("%Y-%m-%d")

    for index in range(len(lines)):
        line = " ".join(lines[index:index + 3])
        for key, label in aliases[sensor_name].items():
            match = re.search(rf"{label}{label_suffix}\s*(?:=|:)?\s*{number}", line, re.I)
            if match:
                coefficients[key] = _number(match.group(1))
                found = True
    if not found:
        raise ValueError(f"No {sensor_name.upper()} coefficients found in {path}")
    sensor["PREDEPLOYMENT_CALIB_COEFFICIENT"] = coefficients


def _parse_navis(lines, suna_cal_f, ph_cal_f=None, ocr_cal_f=None,
                 cdom_cal_f=None, chla_cal_f=None, bbp_cal_f=None):
    sensors = _base_sensors()
    deployment = {"BATTERY_VOLTAGE": 11.6}
    temp_cal, cndc_cal, pres_cal, doxy_cal = {}, {}, {}, {}
    serial = None

    for index, line in enumerate(lines):
        match = re.search(r"Float serial number:\s*(\d+)", line, re.I)
        if match:
            serial = match.group(1)
        match = re.search(r"NAVIS version\D*(\d+)", line, re.I)
        if match:
            deployment["ROM_VERSION"] = match.group(1)
        value = _labeled_digits(line, r"(?:Modem\s+)?(?:ICCID|SIM)")
        if value:
            deployment["SIM"] = value
        value = _labeled_digits(line, r"(?:Modem\s+)?IMEI")
        if value:
            deployment["IMEI"] = value

        match = re.search(r"SBE\s*41N\s*V\s*([\d.]+)\s*SERIAL\s*NO\.\s*(\d+)", line, re.I)
        if match:
            for key in ("temp", "cndc"):
                sensors[key].update(SENSOR_SERIAL_NO=match.group(2),
                                    SENSOR_MODEL="SBE41CP_V" + match.group(1))
        match = re.search(r"Sbe41cpLogCal\(\)\s*temperature_1:\s*(\S+)", line, re.I)
        if match:
            sensors["temp"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(lines[index:index + 5])
            for key in ("TA0", "TA1", "TA2", "TA3"):
                value = _value(block, rf"{key}\s*=\s*(\S+)")
                if value is not None:
                    temp_cal[key] = _number(value)
        match = re.search(r"Sbe41cpLogCal\(\)\s*conductivity:\s*(\S+)", line, re.I)
        if match:
            sensors["cndc"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(lines[index:index + 8])
            for key in ("G", "H", "I", "J", "WBOTC", "CTCOR", "CPCOR"):
                value = _value(block, rf"{key}\s*=\s*(\S+)")
                if value is not None:
                    cndc_cal[key] = _number(value)
        match = re.search(r"Sbe41cpLogCal\(\)\s*pressure\s*S/N\s*=\s*(\d+)", line, re.I)
        if match:
            sensors["pres"]["SENSOR_SERIAL_NO"] = match.group(1)
            date_match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{2})\s*$", line)
            if date_match:
                sensors["pres"]["SENSOR_CALIB_DATE"] = _date(date_match.group(1))
            block = " ".join(lines[index:index + 14])
            for key in ("PA0", "PA1", "PA2", "PTCA0", "PTCA1", "PTCA2",
                        "PTCB0", "PTCB1", "PTCB2", "PTHA0", "PTHA1",
                        "PTHA2", "POFFSET"):
                value = _value(block, rf"{key}\s*=\s*(\S+)")
                if value is not None:
                    pres_cal[key] = _number(value)

        match = re.search(r"pH\s*serial\s*number:\s*\[(\d+-\d+)", line, re.I)
        if match:
            sensors["ph"]["SENSOR_SERIAL_NO"] = match.group(1)

        for label in ("Sbe63", "O2Sens"):
            match = re.search(rf"{label}LogConfig\(\).*?Serial#\D*(\d+)", line, re.I)
            if match:
                sensors["doxy"]["SENSOR_SERIAL_NO"] = match.group(1)
            match = re.search(rf"{label}LogCoef\(\).*?Caldate\s*=\s*(\d+)", line, re.I)
            if match:
                sensors["doxy"]["SENSOR_CALIB_DATE"] = (
                    datetime(2000, 1, 1) + timedelta(days=int(match.group(1)))
                ).strftime("%Y-%m-%d")
            match = re.search(rf"{label}LogConfig\(\).*?Firmware\s*Rev\s*=\s*([\d.]+)", line, re.I)
            if match:
                sensors["doxy"]["SENSOR_MODEL"] = (
                    "SBE63_V" + match.group(1) if label == "O2Sens" else "SBE63_OPTODE"
                )
            for key in ("A0", "A1", "A2", "B0", "B1", "C0", "C1", "C2",
                        "E", "TA0", "TA1", "TA2", "TA3"):
                match = re.search(rf"{label}LogCoef\(\)\s*{key}\s*=\s*(.*)", line, re.I)
                if match:
                    doxy_cal[key] = _number(match.group(1).strip())

        match = re.search(r"MCOMS serial number:\s*\[(\d+)\]", line, re.I)
        if match:
            for key in ("cdom", "chla", "bbp"):
                sensors[key]["SENSOR_SERIAL_NO"] = match.group(1)
        match = re.search(r"IsusConfigLog\(\).*?SUNA Serial\s*Number\s*,\s*SN:(\d+)", line, re.I)
        if match:
            sensors["nitrate"]["SENSOR_SERIAL_NO"] = match.group(1)
        match = re.search(r"H, Calibration\s*File\s*,\s*(\S+)", line, re.I)
        if match:
            sensors["nitrate"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = {
                "calibration file": match.group(1)
            }

    if suna_cal_f:
        _parse_suna_metadata(suna_cal_f, sensors["nitrate"])
        sensors["nitrate"]["PREDEPLOYMENT_CALIB_COEFFICIENT"].update(
            decode_suna_cal(suna_cal_f)
        )
    sensors["temp"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = temp_cal
    sensors["cndc"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = cndc_cal
    sensors["pres"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = pres_cal
    sensors["doxy"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = doxy_cal
    if ph_cal_f:
        _parse_ph_cal(ph_cal_f, sensors["ph"])
    if ocr_cal_f:
        _parse_ocr_cal(ocr_cal_f, sensors.setdefault("ocr", _sensor("OCR", "SATLANTIC", "OCR-504")))
    if cdom_cal_f:
        _parse_optical_cal(cdom_cal_f, sensors["cdom"], "cdom")
    if chla_cal_f:
        _parse_optical_cal(chla_cal_f, sensors["chla"], "chla")
    if bbp_cal_f:
        _parse_optical_cal(bbp_cal_f, sensors["bbp"], "bbp")
    if serial is None:
        raise ValueError("Could not find a NAVIS float serial number in the incoming log")
    return serial, "NAVIS_EBR", deployment, list(sensors.values())


def _parse_solo(lines, suna_cal_f, ctd_cal_f, ph_cal_f, o2_cal_f, ocr_cal_f=None,
                cdom_cal_f=None, chla_cal_f=None, bbp_cal_f=None):
    sensors = _base_sensors("ECO_FLBBCD")
    sensors["ocr"] = _sensor("OCR", "SATLANTIC", "OCR-504", {"calibration file": None})
    deployment = {}
    serial_match = next((re.search(r"BGC SOLO (\d{4})", line, re.I) for line in lines), None)
    if not serial_match:
        raise ValueError("Could not find a BGC SOLO serial number in the incoming log")
    serial = serial_match.group(1)

    ctd_lines = _read_lines(ctd_cal_f)
    for index, line in enumerate(ctd_lines):
        match = re.search(r"SERIALNO=(\d+)", line, re.I)
        if match:
            for key in ("temp", "cndc"):
                sensors[key].update(SENSOR_SERIAL_NO=match.group(1), SENSOR_MODEL="SBE41CP")
        match = re.search(r"TCALDATE=(\S+)", line, re.I)
        if match:
            sensors["temp"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(ctd_lines[index:index + 5])
            sensors["temp"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = {
                key: _number(_value(block, rf"{key}=\s*(\S+)"))
                for key in ("TA0", "TA1", "TA2", "TA3")
            }
        match = re.search(r"CCALDATE=(\S+)", line, re.I)
        if match:
            sensors["cndc"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(ctd_lines[index:index + 8])
            cndc_patterns = {
                "G": "CG", "H": "CH", "I": "CI", "J": "CJ",
                "WBOTC": "WBOTC", "CTCOR": "CTCOR", "CPCOR": "CPCOR",
            }
            sensors["cndc"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = {
                key: _number(_value(block, rf"{pattern}=\s*(\S+)"))
                for key, pattern in cndc_patterns.items()
            }
        match = re.search(r"PCALDATE=(\S+)", line, re.I)
        if match:
            sensors["pres"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(ctd_lines[index:index + 14])
            sensors["pres"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = {
                key: _number(_value(block, rf"{key}=\s*(\S+)"))
                for key in ("PA0", "PA1", "PA2", "PTCA0", "PTCA1", "PTCA2",
                            "PTCB0", "PTCB1", "PTCB2", "PTHA0", "PTHA1",
                            "PTHA2", "POFFSET")
            }

    _parse_ph_cal(ph_cal_f, sensors["ph"])

    o2_lines = _read_lines(o2_cal_f)
    doxy_cal = {}
    for index, line in enumerate(o2_lines):
        match = re.search(r"SERIALNO=(\S+)", line, re.I)
        if match:
            sensors["doxy"].update(SENSOR_SERIAL_NO=match.group(1), SENSOR_MODEL="SBE83_OPTODE")
        match = re.search(r"OxygenCalDate=(\S+)", line, re.I)
        if match:
            sensors["doxy"]["SENSOR_CALIB_DATE"] = _date(match.group(1))
            block = " ".join(o2_lines[index:index + 14])
            for key in ("A0", "A1", "A2", "B0", "B1", "C0", "C1", "C2",
                        "E", "TA0", "TA1", "TA2", "TA3"):
                value = _value(block, rf"{key}=\s*(\S+)")
                if value is not None:
                    doxy_cal[key] = _number(value)
    sensors["doxy"]["PREDEPLOYMENT_CALIB_COEFFICIENT"] = doxy_cal
    if ocr_cal_f:
        _parse_ocr_cal(ocr_cal_f, sensors["ocr"])
    if cdom_cal_f:
        _parse_optical_cal(cdom_cal_f, sensors["cdom"], "cdom")
    if chla_cal_f:
        _parse_optical_cal(chla_cal_f, sensors["chla"], "chla")
    if bbp_cal_f:
        _parse_optical_cal(bbp_cal_f, sensors["bbp"], "bbp")

    _parse_suna_metadata(suna_cal_f, sensors["nitrate"])
    sensors["nitrate"]["PREDEPLOYMENT_CALIB_COEFFICIENT"].update(decode_suna_cal(suna_cal_f))
    return serial, "SOLO_BGC_MRV", deployment, list(sensors.values())


def _send_to_database(serial, platform, deployment, sensors):
    deployment_payload = dict(deployment)
    deployment_payload.setdefault("FLOAT_SERIAL_NO", serial)
    deployment_payload.setdefault("PLATFORM_TYPE", platform)
    deployment_payload.setdefault("ADD_DATE", datetime.now().isoformat())
    # These are optional at deployment creation time. Sensors are submitted
    # separately below as their calibration data becomes available.
    deployment_payload.setdefault("BATTERY_VOLTAGE", None)
    deployment_payload.setdefault("missions", [])
    deployment_payload.setdefault("sensors", [])
    try:
        db.update_deployment(serial, platform, deployment)
        print("Deployment updated successfully.")
    except Exception as error:
        print(f"Deployment update failed: {error}")
        try:
            db.post_deployment(deployment_payload)
            print("Deployment was not registered, so it was added successfully.")
        except Exception as add_error:
            print(f"Deployment add failed: {add_error}")
    for sensor in sensors:
        try:
            db.update_sensor(serial, platform, sensor["SENSOR"], sensor)
            print(f"{sensor['SENSOR']}: updated")
        except Exception as update_error:
            try:
                db.add_sensor(serial, platform, sensor)
                print(f"{sensor['SENSOR']}: added")
            except Exception as add_error:
                print(f"{sensor['SENSOR']}: update failed ({update_error}); add failed ({add_error})")


def _has_coefficients(sensor):
    coefficients = sensor.get("PREDEPLOYMENT_CALIB_COEFFICIENT") or {}
    return any(value is not None for value in coefficients.values())


def _synchronize_ctd_dates(sensors):
    """Use one valid calibration date for the three CTD sensors."""
    ctd_sensors = [
        sensor for sensor in sensors
        if sensor.get("SENSOR") in ("CTD_TEMP", "CTD_CNDC", "CTD_PRES")
    ]
    valid_date = next(
        (
            sensor.get("SENSOR_CALIB_DATE")
            for sensor in ctd_sensors
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(sensor.get("SENSOR_CALIB_DATE", "")))
        ),
        None,
    )
    if valid_date:
        for sensor in ctd_sensors:
            sensor["SENSOR_CALIB_DATE"] = valid_date


def _prompt_for_path(label, current, required=False):
    """Keep a valid configured path or ask for a missing calibration file."""
    current = str(current or "").strip().strip('"')
    if current and Path(current).is_file():
        return current
    while True:
        suffix = " (press Enter to skip)" if not required else ""
        answer = input(f"Path to {label}{suffix}: ").strip().strip('"')
        if not answer:
            if required:
                print(f"{label} is required for this float.")
                continue
            return None
        if Path(answer).is_file():
            return answer
        print(f"File not found: {answer}")


def read_checklog(checklog_f, suna_cal_f, ctd_cal_f=None, ph_cal_f=None,
                  o2_cal_f=None, add_to_db=False, ocr_cal_f=None,
                  prompt_missing=False, cdom_cal_f=None, chla_cal_f=None,
                  bbp_cal_f=None, optics_cal_f=None):
    """Parse a NAVIS/NAVIS-83 or SOLO log.

    The legacy NAVIS call ``read_checklog(log, suna, True)`` remains valid.
    For SOLO, pass CTD, pH and oxygen calibration files as the third, fourth
    and fifth arguments.  Returns ``(serial, platform, deployment, sensors)``.
    """
    if isinstance(ctd_cal_f, bool) and ph_cal_f is None and o2_cal_f is None:
        add_to_db, ctd_cal_f = ctd_cal_f, None
    lines = _read_lines(checklog_f)
    is_solo = bool(re.search(r"BGC SOLO\s+\d{4}", " ".join(lines), re.I))
    shared_optics_cal = optics_cal_f or cdom_cal_f or chla_cal_f or bbp_cal_f
    if is_solo:
        if prompt_missing:
            suna_cal_f = _prompt_for_path("SUNA calibration file", suna_cal_f, required=True)
            ctd_cal_f = _prompt_for_path("CTD calibration file", ctd_cal_f, required=True)
            ph_cal_f = _prompt_for_path("pH calibration file", ph_cal_f, required=True)
            o2_cal_f = _prompt_for_path("oxygen calibration file", o2_cal_f, required=True)
            ocr_cal_f = _prompt_for_path("OCR calibration file", ocr_cal_f)
            shared_optics_cal = _prompt_for_path(
                "shared CDOM/CHLA/BBP calibration PDF", shared_optics_cal
            )
        if not all((ctd_cal_f, ph_cal_f, o2_cal_f)):
            raise ValueError("SOLO logs require CTD, pH and oxygen calibration files")
        if shared_optics_cal:
            cdom_cal_f = chla_cal_f = bbp_cal_f = shared_optics_cal
        result = _parse_solo(lines, suna_cal_f, ctd_cal_f, ph_cal_f, o2_cal_f,
                             ocr_cal_f, cdom_cal_f, chla_cal_f, bbp_cal_f)
    else:
        # First parse the checklog alone so inline coefficients are retained.
        scraped = _parse_navis(lines, None, None, None)
        if prompt_missing:
            scraped_sensors = {sensor["SENSOR"]: sensor for sensor in scraped[3]}
            suna_cal_f = _prompt_for_path("SUNA calibration file", suna_cal_f)
            if not _has_coefficients(scraped_sensors["TRANSISTOR_PH"]):
                ph_cal_f = _prompt_for_path("pH calibration file", ph_cal_f)
            if not ocr_cal_f:
                ocr_cal_f = _prompt_for_path("OCR calibration file", ocr_cal_f)
            shared_optics_cal = _prompt_for_path(
                "shared CDOM/CHLA/BBP calibration PDF", shared_optics_cal
            )
        if shared_optics_cal:
            cdom_cal_f = chla_cal_f = bbp_cal_f = shared_optics_cal
        result = _parse_navis(lines, suna_cal_f, ph_cal_f, ocr_cal_f,
                              cdom_cal_f, chla_cal_f, bbp_cal_f)
    serial, platform, deployment, sensors = result
    for sensor in sensors:
        if sensor.get("SENSOR_CALIB_DATE"):
            sensor["SENSOR_CALIB_DATE"] = _date(sensor["SENSOR_CALIB_DATE"])
    _synchronize_ctd_dates(sensors)
    print(f"Parsed float {serial} ({platform})")
    for sensor in sensors:
        state = "calibration found" if _has_coefficients(sensor) else "no calibration coefficients"
        date = sensor.get("SENSOR_CALIB_DATE", "no calibration date")
        print(f"  {sensor['SENSOR']}: {state}; date={date}")
    if add_to_db:
        _send_to_database(serial, platform, deployment, sensors)
        print("Database update requested.")
    else:
        print("Database update skipped; rerun with --add-to-db to write changes.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklog", nargs="?", default=checklog,
                        help="incoming NAVIS or SOLO log")
    parser.add_argument("suna_cal", nargs="?", default=sunacal,
                        help="SUNA calibration file")
    parser.add_argument("--ctd-cal", default=ctdcal, help="SOLO CTD calibration file")
    parser.add_argument("--ph-cal", default=phcal, help="SOLO pH calibration file")
    parser.add_argument("--o2-cal", default=o2cal, help="SOLO SBE83 oxygen calibration file")
    parser.add_argument("--ocr-cal", default=ocrcal, help="OCR-504 calibration file")
    parser.add_argument("--optics-cal", default=opticscal,
                        help="shared CDOM/CHLA/BBP calibration PDF")
    parser.add_argument("--add-to-db", action="store_true",
                        help="explicitly request the default database update")
    parser.add_argument("--no-db", action="store_true",
                        help="parse and display results without updating the database")
    parser.add_argument("--no-prompt", action="store_true",
                        help="fail instead of asking for missing calibration paths")
    args = parser.parse_args()
    if not args.checklog:
        if args.no_prompt:
            parser.error("Set checklog near the top of the file or provide it as an argument")
        args.checklog = _prompt_for_path("incoming checklog", None, required=True)
    read_checklog(args.checklog, args.suna_cal, args.ctd_cal, args.ph_cal,
                  args.o2_cal, add_to_db=not args.no_db, ocr_cal_f=args.ocr_cal,
                  prompt_missing=not args.no_prompt, optics_cal_f=args.optics_cal)
