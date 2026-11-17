from datetime import datetime
import sys
import pprint
import os
import shutil

"""Reads historical .meta core Argo files and adds to database"""

#import bgc_database
from bgc_database import post_deployment

# Value conforming
vswap = {
    "approximated": "estimated",
    "EXCELL": "FSI",
    "PAINES": "PAINE",
    "Alkaline and lithium": "Lithium and alkaline",
    "as estimated": "estimated",
    "estimate": "estimated",
    "recorded": "as recorded",
    "reported": "as recorded",
    "estimted": "estimated"
}

shipswap = {
    "RV NEIL ARMSTRONG": "NEIL ARMSTRONG",
    "ARMSTRONG": "NEIL ARMSTRONG",
    "RON BROWN": "RONALD H. BROWN",
    "RONALD BROWN": "RONALD H. BROWN",
    "Ronald H. Brown": "RONALD H. BROWN",
    "Ronald Brown": "RONALD H. BROWN",
    "Ronald H Brown": "RONALD H. BROWN",
    "Ron Brown": "RONALD H. BROWN",
    "R/V Ron Brown": "RONALD H. BROWN",
    "NOAA Ron Brown": "RONALD H. BROWN",
    "RONALD H BROWN": "RONALD H. BROWN",
    "SA AGULHAS II": "S.A. AGULHAS II",
    "M/V Maersk Visby": "MAERSK VISBY",
    "LAURENCE M GOULD": "LAURENCE M. GOULD",
    "M/V Lykes Raider": "LYKES RAIDER",
    "M/V Maersk Hong Kong": "MAERSK HONG KONG",
    "Lykes Runner": "LYKES RUNNER",
    "M/V Lykes Runner": "LYKES RUNNER",
    "M/V Lykes Commander": "LYKES COMMANDER",
    "M/V Lykes Energizer": "LYKES ENERGIZER",
    "CMV Oleander": "OLEANDER",
    "CMV OLEANDER": "OLEANDER",
    "Ever Garden": "MV EVER GARDEN",
    "Horizon Hawaii": "HAWAII",
    "Horizon HAwaii": "HAWAII",
    "Revelle": "ROGER REVELLE",
    "SA Agulhas": "S.A. AGULHAS",
    "Agulhas": "S.A. AGULHAS",
    "Templeman": "WILFRED TEMPLEMAN",
    "CGM Pasteur": "CGA PASTEUR",
    "Pasteur": "CGA PASTEUR",
    "Akedemic Vavilov": "AKADEMIK SERGEY VAVILOV",
    "Gaining": "EVER GAINING",
    "M/V Gaining": "EVER GAINING",
    "ARA Almirante Irizar": "ALMIRANTE IRIZAR",
    "USCG Polar Sea": "USCGC POLAR SEA",
    "Tridente": "RBAM TRIDENTE",
    "Hapag-Lloyd Madrid Express": "MADRID EXPRESS",
    "M/V Alianca Maua": "ALIANCA MAUA",
    "Weatherbird": "WEATHERBIRD II",
    "SWIFT": "SWIFT ACE",
    "M/V Safmarine Gonubie": "SAFMARINE GONUBIE",
    "NPo Maximiano": "ALMIRANTE MAXIMIANO",
    "M/V Maersk Vilnius": "MAERSK VILNIUS",
    "Louis St. Laurent": "LOUIS S. ST. LAURENT",
    "M/V Madrid Express": "MADRID EXPRESS",
    "M/V Safmarine Oranje": "S.A. ORANJE",
    "M/V Safmarine Ngami": "SAFMARINE NGAMI",
    "Thomas Thompson": "THOMAS G. THOMPSON",
    "SSV Corwith Cramer": "CORWITH CRAMER",
    "Akademik Sergey Vavilo": "AKADEMIK SERGEY VAVILOV",
    "Akademik Vavilov": "AKADEMIK SERGEY VAVILOV",
    "Hapag Lloyd Rome Express": "ROME EXPRESS",
    "Maria Merian": "MARIA S. MERIAN",
    "RV SA Agulhas": "S.A. AGULHAS",
    "RSS SA Agulhas": "S.A. AGULHAS",
    "Knorr SALP": "KNORR",
    "Knorr SLAP": "KNORR",
    "MY Alucia": "MV ALUCIA",
    "FRS Algoa": "ALGOA",
    "SSV CORWITH CRAMER": "CORWITH CRAMER",
    "SPROUL": "ROBERT GORDON SPROUL",
    "CMA CGN RABELAIS": "CMA CGM RABELAIS",
    "THOMAS G THOMPSON": "THOMAS G. THOMPSON",
    "USCGC HEALY": "HEALY"
}


# Field name conforming
swap = {
    'initial battery voltage [volt]': 'initial battery voltage',
    'salinity calibration date': 'conductivity calibration date'
}

# Argo platform types
r23_key = {
    "204": "S2A",
    "202": "SOLO_II",
}


def read_and_add(fname):
    # try:
    # Read file
    meta = {}
    with open(base_dir + 'in/' + fname) as f:
        Lines = f.readlines()
        for line in Lines:
            # Unknowns
            if line[40:].strip() in ('n/a', 'unknown', '', '-999.', '99 99 9999 99 99', '99. 99. 999. 999.'):
                meta[line[:40].strip()] = None
            else:
                meta[line[:40].strip()] = line[40:].strip()

    # Current datetime
    now = datetime.now()
    crt_datetime = now.isoformat()

    # Convert degree decimal minutes to decimal degrees, ignore if None
    if meta['launch position [lat latm lon lonm]']:
        lat_deg, lat_m, long_deg, long_m = meta['launch position [lat latm lon lonm]'].split(
        )

        lat_deg = float(lat_deg)
        lat_m = float(lat_m)
        long_deg = float(long_deg)
        long_m = float(long_m)

        lat_dd = lat_deg + lat_m/60
        long_dd = long_deg + long_m/60
    else:
        lat_dd = None
        long_dd = None

    # Convert datetime
    if meta['start time [dd mm yyyy hh mm (Z)]']:
        START_DATE = datetime.strptime(
            meta['start time [dd mm yyyy hh mm (Z)]'], "%d %m %Y %H %M").isoformat()
    else:
        START_DATE = None

    if meta['launch time [dd mm yyyy hh mm (Z)]']:
        LAUNCH_DATE = datetime.strptime(
            meta['launch time [dd mm yyyy hh mm (Z)]'], "%d %m %Y %H %M").isoformat()
    else:
        LAUNCH_DATE = None

    if meta['pressure calibration date']:
        try:
            pres_cal_date = datetime.strptime(
                meta['pressure calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
        except:
            try:
                pres_cal_date = datetime.strptime(
                    meta['pressure calibration date'], "%d-%b-%y").strftime("%Y-%m-%d")
            except:
                try:
                    pres_cal_date = datetime.strptime(
                        meta['pressure calibration date'], "%d %m %y").strftime("%Y-%m-%d")
                except:
                    try:
                        pres_cal_date = datetime.strptime(
                            meta['pressure calibration date'], "%Y%m%d").strftime("%Y-%m-%d")
                    except:
                        raise Exception("error in pres cal date")
    else:
        pres_cal_date = None

    if meta['temperature calibration date']:
        try:
            temp_cal_date = datetime.strptime(
                meta['temperature calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
        except:
            try:
                temp_cal_date = datetime.strptime(
                    meta['temperature calibration date'], "%d-%b-%y").strftime("%Y-%m-%d")
            except:
                try:
                    temp_cal_date = datetime.strptime(
                        meta['temperature calibration date'], "%d %m %y").strftime("%Y-%m-%d")
                except:
                    try:
                        temp_cal_date = datetime.strptime(
                            meta['temperature calibration date'], "%Y%m%d").strftime("%Y-%m-%d")
                    except:
                        raise Exception("error in temp cal date")
    else:
        temp_cal_date = None

    # Fix field names
    meta_f = {}
    for key, value in meta.items():
        try:
            meta_f[swap[key]] = value  # Swap for new key if exist
        except:
            meta_f[key] = value

    # Fix values
    meta_c = {}
    for key, value in meta_f.items():
        try:
            meta_c[key] = vswap[value]  # Swap for new value exists
        except:
            meta_c[key] = value

    if meta_c['conductivity calibration date']:
        try:
            cond_cal_date = datetime.strptime(
                meta_c['conductivity calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
        except:
            try:
                cond_cal_date = datetime.strptime(
                    meta_c['conductivity calibration date'], "%d-%b-%y").strftime("%Y-%m-%d")
            except:
                try:
                    cond_cal_date = datetime.strptime(
                        meta_c['conductivity calibration date'], "%d %m %y").strftime("%Y-%m-%d")
                except:
                    try:
                        cond_cal_date = datetime.strptime(
                            meta_c['conductivity calibration date'], "%Y%m%d").strftime("%Y-%m-%d")
                    except:
                        raise Exception("error in cndc cal date")
    else:
        cond_cal_date = None

    # Platform makers
    platform_maker_key = {
        "Webb": "TWR",
        "Teledyne Webb Research": "TWR",
        "Teledyne- Webb Research": "TWR"
    }
    try:
        platform_maker = platform_maker_key[meta_c['float manufacturer']]
    except:
        platform_maker = meta_c['float manufacturer'].upper()

    # Deployment platform
    try:
        ship = shipswap[meta_c['deployment platform'].strip()]
    except:
        if meta_c['deployment platform']:
            ship = meta_c['deployment platform'].upper().replace(
                "M/V ", "").replace("FRS ", "").replace("SSV ", "").replace("RSS ", "").replace("R/V ", "")
        else:
            ship = None

    # PRES Sensor models
    try:
        pres_sensor_model = meta_c['ref table pressure SENSOR_TYPE']
    except:
        # Kistler 2900PSIA
        if meta_c.get('pressure sensor manufacturer') == 'Kistler' and meta_c.get('pressure sensor type') == '2900 psia':
            pres_sensor_model = 'KISTLER_2900PSIA'
        if meta_c['pressure sensor type']:
            if meta_c.get('pressure sensor manufacturer').upper() == 'DRUCK' and meta_c.get('pressure sensor type').upper() == '2900 PSIA':
                pres_sensor_model = 'DRUCK_2900PSIA'
        else:
            pres_sensor_model = meta_c.get('pressure sensor type')

    # PRES sensor makers
    pres_maker_key = {
        "Paines": "PAINE"
    }
    try:
        pres_sensor_maker = pres_maker_key[meta_c['pressure sensor manufacturer']]
    except:
        pres_sensor_maker = meta_c['pressure sensor manufacturer'].upper()

    # TEMP models
    try:
        temp_sensor_model = meta_c['ref table temperature SENSOR_TYPE']
    except:
        temp_sensor_model = meta_c['temperature sensor type'].upper()

    # CNDC models
    try:
        cndc_sensor_model = meta_c['ref table conductivity SENSOR_TYPE']
    except:
        cndc_sensor_model = meta_c['conductivity sensor type'].upper()

    # Battery voltage initial
    try:
        init_bat_volt = meta_c.get(
            'initial battery voltage').replace("V", "").strip()
    except:
        init_bat_volt = None

    try:
        bat_manufacturer, bat_model = meta_c.get(
            'battery manufacturer/model').split()
    except:
        bat_manufacturer = None
        bat_model = None

    aoml_key = {
        "SOLO_TS16": "SOLO_W",
        "ALTOIR_TS12": "ALTO",
        "SOLO_TS2": "SOLO_W",
        "SOLO_TS9": "SOLO_W",
        "SOLOOF_TS10": "SOLO_W",
        "SOLO_TS14": "SOLO_W",
        "SOLO_TS23": "SOLO_W",
        "SOLOIR_TS2": "SOLO_W",
        "SOLOIR_TSO5": "SOLO_W",
        "SOLO2IR_TS9": "S2A",
        "SOLO2IR_TS36": "S2A",
        "APEXIR_TS3": "APEX",
        "APEXIR_TSBIO24": "APEX"
    }
    # Platform type
    try:  # ref table field is preferend, not in all meta files
        platform_type = r23_key[meta_c['ref table PLATFORM_TYPE']]
    except:  # Convert wmo if ref table not available
        platform_type = aoml_key[meta_c['instrument type']]

    data = {
        "ADD_DATE": crt_datetime,
        "AOML_ID": meta_c['internal ID number'],
        "PLATFORM_NUMBER": meta_c['WMO ID number'],
        "FLOAT_SERIAL_NO": meta_c['float serial number'],
        "PLATFORM_MAKER": platform_maker,
        "PLATFORM_TYPE": platform_type,
        "PLATFORM_TYPE_WMO": meta_c['WMO instrument type (table 1770)'],
        "PLATFORM_TYPE_AOML": meta_c['instrument type'],
        "WMO_RECORDER_TYPE": meta_c['WMO recorder type (table 4770)'],
        "TRANS_SYSTEM": meta_c['transmission type'],
        "START_DATE": START_DATE,
        "START_DATE_QC": meta_c['status of start time'],
        "LAUNCH_DATE": LAUNCH_DATE,
        "LAUNCH_DATE_QC": meta_c['status of launch time'],
        "LAUNCH_LATITUDE": lat_dd,
        "LAUNCH_LONGITUDE": long_dd,
        "LAUNCH_POSITION_QC": meta_c['status of launch position'],
        "PI_NAME": meta_c['PI'],
        "PI_ADDRESS": meta_c['principal investigator address'],
        "ORIGIN_COUNTRY": meta_c['originating country'],
        "DEPLOYER": meta_c['float deployer'],
        "DEPLOYER_ADDRESS": meta_c['float deployer address'],
        "DEPLOYMENT_PLATFORM": ship,
        "DEPLOYMENT_CRUISE_ID": meta_c['deployment cruise id'],
        "DEPLOYMENT_REFERENCE_STATION_ID": meta_c.get('profile at deployment'),
        "FLOAT_CONTROLLER_SERIAL_NO": meta_c.get('CPU serial number'),
        "ROM_VERSION": meta_c['ROM version'],
        "BATTERY_TYPE": meta_c['battery type'],
        "BATTERY_MANUFACTURER": bat_manufacturer,
        "BATTERY_MODEL": bat_model,
        "BATTERY_SERIAL_NO": meta_c.get('CPU battery serial number'),
        "BATTERY_VOLTAGE": init_bat_volt,
        "BATTERY_PACKS": meta_c.get('battery packs'),
        "BATTERY_DETAILS": meta_c.get('battery details'),
        "PUMP_BATTERY_SERIAL_NO": meta_c.get('pump battery serial number'),

        "NOMINAL_DRIFT_PRES": meta_c["nominal drift pressure [dbar]"],
        "CYCLES_FOR_DRIFT_PRES": meta_c["cycles for drift pressure"],
        "NOMINAL_PROFILE_PRES": meta_c["nominal profile pressure [dbar]"],
        "CYCLES_FOR_PROFILE_PRES": meta_c["cycles for profile pressure"],
        "PROFILE_SAMPLING_METHOD": meta_c["Profile Sampling Method"],
        "PROFILE_SAMPLING_METHOD_2": meta_c.get("Profile Sampling Method(2)"),

        "CUSTOMIZATION": meta_c.get('customization'),
        "COMMENTS": meta_c['comment'],
        "HISTORICAL": True,
        "missions": [],
        "sensors": [
            {
                "ADD_DATE":  crt_datetime,
                "SENSOR": 'CTD_PRES',
                "SENSOR_MAKER": pres_sensor_maker,
                "SENSOR_MODEL": pres_sensor_model,
                "SENSOR_SERIAL_NO": meta_c['pressure sensor serial number'],
                "SENSOR_CALIB_DATE": pres_cal_date,
                "PREDEPLOYMENT_CALIB_EQUATION": {'eq1': None},
            },
            {
                "ADD_DATE":  crt_datetime,
                "SENSOR": 'CTD_TEMP',
                "SENSOR_MAKER": meta_c['temperature sensor manufacturer'].upper(),
                "SENSOR_MODEL": temp_sensor_model,
                "SENSOR_SERIAL_NO": meta_c['temperature sensor serial number'],
                "SENSOR_CALIB_DATE":  temp_cal_date,
                "PREDEPLOYMENT_CALIB_EQUATION": {'eq1': None},
            },
            {
                "ADD_DATE":  crt_datetime,
                "SENSOR": 'CTD_CNDC',
                "SENSOR_MAKER": meta_c['conductivity sensor manufacturer'].upper(),
                "SENSOR_MODEL": cndc_sensor_model,
                "SENSOR_SERIAL_NO": meta_c['conductivity sensor serial number'],
                "SENSOR_CALIB_DATE": cond_cal_date,
                "PREDEPLOYMENT_CALIB_EQUATION": {'eq1': None},
            },
        ]
    }

    #pp = pprint.PrettyPrinter(indent=1)
    # pp.pprint(data)
    post_deployment(data)

    # if sucessfull up to this point, move file to "out" folder
    shutil.move(base_dir + 'in/' + fname, base_dir + 'out/' + fname)
    print("Added: ", fname)

    # except:
    #     e = sys.exc_info()
    #     print("Fail: ", fname)
    #     print(e[0], e[1])


# Start program
if __name__ == '__main__':
    base_dir = 'assets/metadata/'
    fnames = os.listdir(base_dir + 'in')

    for f in fnames:
        read_and_add(f)
