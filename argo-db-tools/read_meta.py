from datetime import datetime
import json
import pprint

import bgc_database

fname = 'assets/metadata/7571_007539.meta'

#Read file
meta = {}
with open(fname) as f:
    Lines = f.readlines()
    for line in Lines:
        #Unknowns
        if line[40:].strip() in ('n/a','unknown','','-999.','99 99 9999 99 99','99. 99. 999. 999.'):
            meta[line[:40].strip()] = None
        else:
            meta[line[:40].strip()] = line[40:].strip()

#Parse sensor coefficient fields to json
def coef_parser(field):
    coefs = meta[field].replace(' ','').strip(';').split(';')
    coef_dict = {}
    for coef in coefs:
        key, value = coef.split('=')
        coef_dict[key] = float(value)

    #print(json.dumps(coef_dict))
    return (coef_dict)


#Current datetime
now = datetime.now()
crt_datetime = now.isoformat()

#Convert degree decimal minutes to decimal degrees, ignore if None
if meta['launch position [lat latm lon lonm]']:
    lat_deg, lat_m, long_deg, long_m = meta['launch position [lat latm lon lonm]'].split(" ")

    lat_deg = float(lat_deg)
    lat_m = float(lat_m)
    long_deg = float(long_deg)
    long_m = float(long_m)

    lat_dd = lat_deg + lat_m/60
    long_dd = long_deg + long_m/60
else:
    lat_dd = None
    long_dd = None

#Convert datetime
if meta['start time [dd mm yyyy hh mm (Z)]']:
    START_DATE = datetime.strptime(meta['start time [dd mm yyyy hh mm (Z)]'], "%d %m %Y %H %M").isoformat()
else:
    START_DATE = None

if meta['launch time [dd mm yyyy hh mm (Z)]']:
    LAUNCH_DATE = datetime.strptime(meta['launch time [dd mm yyyy hh mm (Z)]'], "%d %m %Y %H %M").isoformat()
else:
    LAUNCH_DATE = None

if meta['pressure calibration date']:
    pres_cal_date = datetime.strptime(meta['pressure calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
else:
    pres_cal_date = None

if meta['temperature calibration date']:
    temp_cal_date = datetime.strptime(meta['temperature calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
else:
    temp_cal_date = None

if meta['conductivity calibration date']:
    cond_cal_date = datetime.strptime(meta['conductivity calibration date'], "%d %m %Y").strftime("%Y-%m-%d")
else:
    cond_cal_date = None

#Field name conforming
swap = {
    'initial battery voltage [volt]':'initial battery voltage'
}

meta_c = {}
for key, value in meta.items():
    try:
        meta_c[swap[key]] = value #Swap for new key if exist
    except:
        meta_c[key] = value

data = {
    "ADD_DATE": crt_datetime,
    "AOML_ID": meta_c['internal ID number'],
    "PLATFORM_NUMBER": meta_c['WMO ID number'],
    "FLOAT_SERIAL_NO": meta_c['float serial number'],
    "PLATFORM_MAKER": meta_c['float manufacturer'],
    "PLATFORM_TYPE": meta_c['ref table PLATFORM_TYPE'],
    "INST_TYPE": meta_c['instrument type'],
    "WMO_INST_TYPE": meta_c['WMO instrument type (table 1770)'],
    "WMO_RECORDER_TYPE": meta_c['WMO recorder type (table 4770)'],
    "TRANS_SYSTEM": meta_c['transmission type'],
    "TRANS_FREQUENCY": meta_c['transmission repetition rate [sec]'],
    "IRIDIUM_PROGRAM_NO": meta_c['IRIDIUM program number'],
    "START_DATE": START_DATE,
    "START_DATE_QC": meta_c['status of start time'],
    "LAUNCH_DATE": LAUNCH_DATE,
    "LAUNCH_DATE_QC": meta_c['status of launch time'],
    "LAUNCH_LATITUDE": lat_dd,
    "LAUNCH_LONGITUDE": long_dd,
    "LAUNCH_POSITION_QC": meta_c['status of launch position'],
    "PROJECT_NAME": meta_c['ref table PROJECT_NAME'],
    "PI_NAME": meta_c['PI'],
    "PI_ADDRESS": meta_c['principal investigator address'],
    "ORIGIN_COUNTRY": meta_c['originating country'],
    "DEPLOYER": meta_c['float deployer'],
    "DEPLOYER_ADDRESS": meta_c['float deployer address'],
    "DEPLOYMENT_TYPE": meta_c['deployment type'],
    "DEPLOYMENT_PLATFORM": meta_c['deployment platform'],
    "DEPLOYMENT_CRUISE_ID": meta_c['deployment cruise id'],
    "DEPLOYMENT_REFERENCE_STATION_ID": meta_c['profile at deployment'],
    "DEPLOYMENT_PLATFORM_ID": meta_c['ref table DEPLOYMENT_PLATFORM_ID'],
    "PTT": meta_c['transmission ID number'],
    "CPU_SERIAL_NO": None,
    "ROM_VERSION": meta_c['ROM version'],
    "BATTERY_TYPE": meta_c['battery type'],
    "BATTERY_MANUFACTURER": 'Electrochem',
    "BATTERY_MODEL":'3PD1404',
    "BATTERY_SERIAL_NO": None,
    "BATTERY_VOLTAGE": meta_c['initial battery voltage'],
    "BATTERY_PACKS": meta_c.get('battery packs'),
    "BATTERY_DETAILS": meta_c.get('battery details'),
    "PUMP_BATTERY_SERIAL_NO": None,
    "CUSTOMIZATION": meta_c['customisation'],
    "COMMENTS":meta_c['comment'],
    "missions": [],
    "sensors": [
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'CTD_PRES',
            "SENSOR_MAKER": meta_c['pressure sensor manufacturer'],
            "SENSOR_MODEL": meta_c['ref table pressure SENSOR_TYPE'],
            "SENSOR_SERIAL_NO": meta_c['pressure sensor serial number'],
            "SENSOR_CALIB_DATE": pres_cal_date,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for pressure']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for pressure'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'CTD_TEMP',
            "SENSOR_MAKER": meta_c['temperature sensor manufacturer'],
            "SENSOR_MODEL": meta_c['ref table temperature SENSOR_TYPE'],
            "SENSOR_SERIAL_NO": meta_c['temperature sensor serial number'],
            "SENSOR_CALIB_DATE":  temp_cal_date,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for temperature']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for temperature'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'CTD_CNDC',
            "SENSOR_MAKER": meta_c['conductivity sensor manufacturer'],
            "SENSOR_MODEL": meta_c['ref table conductivity SENSOR_TYPE'],
            "SENSOR_SERIAL_NO": meta_c['conductivity sensor serial number'],
            "SENSOR_CALIB_DATE": cond_cal_date,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for salinity']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for salinity'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'CPU_VOLTAGE',
            "SENSOR_MAKER": None,
            "SENSOR_MODEL": None,
            "SENSOR_SERIAL_NO": None,
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for cpu voltage']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for cpu voltage'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'PUMP_VOLTAGE',
            "SENSOR_MAKER": None,
            "SENSOR_MODEL": None,
            "SENSOR_SERIAL_NO": None,
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for pump voltage']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for pump voltage'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'OPTODE_DOXY',
            "SENSOR_MAKER": meta_c['oxygen sensor manufacturer'],
            "SENSOR_MODEL": meta_c['oxygen sensor type'],
            "SENSOR_SERIAL_NO": meta_c['oxygen sensor serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": {'eq1':meta_c['calib eq 1 for oxygen'], 
                'eq2':meta_c['calib eq 2 for oxygen'],
                'eq3':meta_c['calib eq 3 for oxygen'],
                'eq4':meta_c['calib eq 4 for oxygen'],
                'eq5':meta_c['calib eq 5 for oxygen'],
                'eq6':meta_c['calib eq 6 for oxygen'],
                'eq7':meta_c['calib eq 7 for oxygen'],
                'eq8':meta_c['calib eq 8 for oxygen'],
                'eq9':meta_c['calib eq 9 for oxygen']},
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for oxygen'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'TRANSISTOR_PH',
            "SENSOR_MAKER": meta_c['ph sensor manufacturer'],
            "SENSOR_MODEL": meta_c['ph sensor type'],
            "SENSOR_SERIAL_NO": meta_c['ph sensor serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": None,
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for pH'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'FLUOROMETER_CHLA',
            "SENSOR_MAKER": meta_c['fluorometer manufacturer'],
            "SENSOR_MODEL": meta_c['fluorometer sensor type'],
            "SENSOR_SERIAL_NO": meta_c['fluorometer serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": None,
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for chla'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'BACKSCATTERINGMETER_BBP700',
            "SENSOR_MAKER": meta_c['fluorometer manufacturer'],
            "SENSOR_MODEL": meta_c['fluorometer sensor type'],
            "SENSOR_SERIAL_NO": meta_c['fluorometer serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": None,
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for bbp700'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'FLUOROMETER_CDOM',
            "SENSOR_MAKER": meta_c['fluorometer manufacturer'],
            "SENSOR_MODEL": meta_c['fluorometer sensor type'],
            "SENSOR_SERIAL_NO": meta_c['fluorometer serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": None,
            "PREDEPLOYMENT_CALIB_COEFFICIENT": coef_parser('calib coef for cdom'),
            "COMMENTS":None
        },
        {
            "ADD_DATE":  crt_datetime,
            "SENSOR": 'SPECTROPHOTOMETER_NITRATE',
            "SENSOR_MAKER": meta_c['nitrate sensor manufacturer'],
            "SENSOR_MODEL": meta_c['nitrate sensor type'],
            "SENSOR_SERIAL_NO": meta_c['nitrate sensor serial number'],
            "SENSOR_CALIB_DATE": None,
            "PREDEPLOYMENT_CALIB_EQUATION": None,
            "PREDEPLOYMENT_CALIB_COEFFICIENT": None,
            "COMMENTS":None
        },
    ]
}


# pp = pprint.PrettyPrinter(indent=1)
# pp.pprint(data)

#add_deployment(data)