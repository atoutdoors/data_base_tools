import tomllib
import json
import os
from pathlib import Path
from bgc_database import update_sensor
from dotenv import load_dotenv
print("Load ENV")
load_dotenv()
print('ENV ')
# Tools to interact with database


BASE_URL = os.getenv("BASE_URL")
#BASE_URL = "http://127.0.0.1:8000"

TOKEN = os.getenv("TOKEN")
GOOGLEDRIVE = os.getenv("GOOGLEDRIVE")
FLOAT_ROOT = Path(GOOGLEDRIVE) / "Shared drives" / "WHOI Argo" / "BGC" / "Floats"


def ph_meta(phcal_path): 
    """_summary_

    Args:
        phcal_path (_type_): _description_

    Returns:
        _type_: _description_
    """
    with phcal_path.open("rb") as f:
        data = tomllib.load(f)
    try:
        data['fP']['fP_poly_order'] = data['fP']['poly_order']
        data['K2P']['K2P_poly_order'] = data['K2P']['poly_order']
        meta = data['Instrument'] | data['K0'] | data['fP'] | data['K2P']  
        meta['K0_calibration_date'] = data['K0']['K0_calibration_date'].strftime("%Y-%m-%d")
        return json.dumps(meta)
    except:
        print('failed to parse ' + phcal_path)
        return False


def add_ph_meta(FLOAT_SERIAL_NO,PLATFORM_TYPE='NAVIS_EBR'):
    SENSOR = 'TRANSISTOR_PH'
    phcal_path = list((FLOAT_ROOT / FLOAT_SERIAL_NO /  "sensor_cal" / "pH").glob("*.cal"))
    if phcal_path:
        meta = ph_meta(phcal_path[0])
        print(meta)
        update_sensor(int(FLOAT_SERIAL_NO), PLATFORM_TYPE, SENSOR, meta)
    else:
        print('pH .cal file not found')