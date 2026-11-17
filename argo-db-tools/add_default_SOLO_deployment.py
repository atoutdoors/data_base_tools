from bgc_database import post_deployment
from datetime import datetime
import os
# Manually adds a float to the database
# You do not need to explicitly input None for a blank field, you can just leave it out.

FLOAT_SERIAL_NO = 4057
#############


now = datetime.now()
crt_datetime = now.isoformat()


data = {
    "ADD_DATE": crt_datetime,
    "INTERNAL_ID_NO": None,
    "PLATFORM_NUMBER": None,
    "FLOAT_SERIAL_NO": FLOAT_SERIAL_NO,
    "PLATFORM_MAKER": "MRV",
    "PLATFORM_TYPE": "SOLO_BGC_MRV",
    "INST_TYPE": None,
    "INSTITUTION":"WHOI",
    "FUNDER":"GO-BGC",
    "WMO_INST_TYPE": None,
    "WMO_RECORDER_TYPE": None,
    "TRANS_SYSTEM_ID": None,
    "TRANS_SYSTEM": "IRIDIUM",
    "MODEM_TYPE": "Civilian",
    "IRIDIUM_PROGRAM_NO": None,
    "START_DATE": None,
    "START_DATE_QC": "estimated",
    "LAUNCH_DATE": None,
    "LAUNCH_DATE_QC": "estimated",
    "LAUNCH_LATITUDE": None,
    "LAUNCH_LONGITUDE": None,
    "LAUNCH_POSITION_QC": "estimated",
    "PROJECT_NAME": None,
    "PI_NAME": "Nicholson, Wijffels",
    "PI_ADDRESS": "WHOI, Woods Hole, MA",
    "ORIGIN_COUNTRY": "USA",
    "DEPLOYER": None,
    "DEPLOYER_ADDRESS": None,
    "DEPLOYMENT_TYPE": None,
    "DEPLOYMENT_PLATFORM": None,
    "DEPLOYMENT_CRUISE_ID": None,
    "DEPLOYMENT_REFERENCE_STATION_ID": None,
    "DEPLOYMENT_PLATFORM_ID": None,
    "PTT": None,
    "CPU_SERIAL_NO": None,
    "ROM_VERSION": None,
    "BATTERY_TYPE": "Lithium",
    "BATTERY_MANUFACTURER": "Electrochem",
    "BATTERY_SERIAL_NO": None,
    "BATTERY_VOLTAGE": 12,
    "BATTERY_PACKS": 6,
    "BATTERY_DETAILS": None,
    "PUMP_BATTERY_SERIAL_NO": None,
    "NOMINAL_DRIFT_PRES": 1000,
    "CYCLES_FOR_DRIFT_PRES": 1,
    "NOMINAL_PROFILE_PRES": 2000,
    "CYCLES_FOR_PROFILE_PRES": 1,
    "PROFILE_SAMPLING_METHOD": "Primary sampling: mixed [deeper than nominal 985dbar: discrete; nominal 985dbar to surface: 2dbar-bin averaged sampled at 1.0 Hz]",
    "PROFILE_SAMPLING_METHOD_2": "Secondary sampling: discrete",
    "CUSTOMIZATION": None,
    "COMMENTS": None,
    "missions": [],
    "sensors": []
}

results = post_deployment(data)
