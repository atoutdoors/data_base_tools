import re
import pandas as pd
import os


def decode_suna_cal(suna_cal):
    """Decodes .cal file for SUNA in preperation for adding info to database"""

    cal = {}

    data_start_line = None

    # Defaults
    cal['BR_WL_OFFSET'] = 210  # Bromide wavelength offset
    cal['BR_PRES_COEF'] = 0.0265  # Bromide Pressure coefficient

    with open(suna_cal, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):

            # Other info here...
            # Calibration temperature
            mo = re.match("H,T_CAL (\d*.\d*)", line)
            if mo:
                cal['CAL_TEMP'] = float(mo.group(1))

            # Start of data
            mo = re.match("E", line)
            if mo and not data_start_line:
                data_start_line = i
                break

    # Calibration data
    columns = ['H', 'WAVELENGTH', 'NO3', 'SWA', 'TSWA', 'REFERENCE']
    cal_data = pd.read_csv(suna_cal, skiprows=data_start_line, names=columns)

    cal["WAVELENGTH"] = cal_data.WAVELENGTH.to_list()
    cal["NO3"] = cal_data.NO3.to_list()
    cal["SWA"] = cal_data.SWA.to_list()
    cal["TSWA"] = cal_data.TSWA.to_list()
    cal["REFERENCE"] = cal_data.REFERENCE.to_list()
    cal["calibration file"] = os.path.basename(suna_cal)

    return cal


if __name__ == "__main__":
    cal = decode_suna_cal(
        r"G:\Shared drives\WHOI Argo\BGC\Floats\1203\sensor_cal\SUNA\Calibration\SNA1494C.cal")
    print(cal)
