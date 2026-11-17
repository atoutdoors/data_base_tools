from bgc_database import post_deployment
from datetime import datetime
import os

"""Adds a template entry to database with static fields filled in. Change "FLOAT_SERIAL_NO" to desired new float's SN"""

FLOAT_SERIAL_NO = 2018
#############


now = datetime.now()
crt_datetime = now.isoformat()

data = {
    "ADD_DATE": crt_datetime,
    "INTERNAL_ID_NO": None,
    "PLATFORM_NUMBER": None,
    "FLOAT_SERIAL_NO": FLOAT_SERIAL_NO,
    "DEATH_DATE": None,
    "WHOI_TAG": None,
    "PURCHASE_ORDER": None,
    "PLATFORM_MAKER": "SBE",
    "PLATFORM_TYPE": "NAVIS_EBR",
    "PLATFORM_TYPE_AOML": "NAVISIR_TSOPJ1",
    "PLATFORM_TYPE_WMO": 869,
    "WMO_RECORDER_TYPE": 64,
    "DRY_WEIGHT": None,
    "TRANS_SYSTEM": "IRIDIUM",
    "MODEM_TYPE": "Civilian",
    "MODEM_SERIAL_NO": None,
    "IMEI": None,
    "SIM": None,
    "START_DATE": None,
    "START_DATE_QC": None,
    "LAUNCH_DATE": None,
    "LAUNCH_DATE_QC": None,
    "LAUNCH_LATITUDE": None,
    "LAUNCH_LONGITUDE": None,
    "LAUNCH_POSITION_QC": None,
    "INSTITUTION": "WHOI",
    "FUNDER": "GO-BGC",
    "PI_NAME": "Nicholson, Wijffels",
    "PI_ADDRESS": "WHOI, Woods Hole, MA",
    "ORIGIN_COUNTRY": "USA",
    "DEPLOYER": None,
    "DEPLOYER_ADDRESS": None,
    "DEPLOYMENT_PLATFORM": None,
    "DEPLOYMENT_CRUISE_ID": None,
    "DEPLOYMENT_REFERENCE_STATION_ID": None,
    "DEPLOYMENT_MOB": None,
    "DEPLOYMENT_PORT": None,
    "FLOAT_CONTROLLER_SERIAL_NO": None,
    "GPS_SERIAL_NO": None,
    "ROM_VERSION": None,
    "BATTERY_TYPE": "Lithium",
    "BATTERY_MANUFACTURER": "Electrochem",
    "BATTERY_MODEL": "3PD1404",
    "BATTERY_SERIAL_NO": None,
    "BATTERY_VOLTAGE": None,
    "BATTERY_PACKS": "3DD Li",
    "BATTERY_DETAILS": "4 packs of 3DD cell",
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
