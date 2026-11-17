from ctypes.wintypes import FLOAT
import re
from datetime import datetime, timedelta
import bgc_database as db
from decode_suna_cal import decode_suna_cal


def read_checklog(checklog_f, suna_cal_f, ctd_cal_f,ph_cal_f, o2_cal_f, add_to_db=False):
    """Parses tera term log of checklog commands for preperation to add to BGC database
    checklog_f = string, file directory
    returns meta = dictionary of metadata"""

    now = datetime.now()
    crt_datetime = now.isoformat()

    deployment = {}

    ctd_temp = {"SENSOR": "CTD_TEMP",
                "SENSOR_MAKER": "SBE",
                "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                "PREDEPLOYMENT_CALIB_COEFFICIENT": None,
                "ADD_DATE": crt_datetime
                }

    ctd_cndc = {"SENSOR": "CTD_CNDC",
                "SENSOR_MAKER": "SBE",
                "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                "PREDEPLOYMENT_CALIB_COEFFICIENT": None,
                "ADD_DATE": crt_datetime
                }

    ctd_pres = {"SENSOR": "CTD_PRES",
                "SENSOR_MAKER": "DRUCK",
                "SENSOR_MODEL": "DRUCK_2900PSIA",
                "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                "PREDEPLOYMENT_CALIB_COEFFICIENT": None,
                "ADD_DATE": crt_datetime
                }
    optode_doxy = {"SENSOR": "OPTODE_DOXY",
                   "SENSOR_MAKER": "SBE",
                   "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                   "ADD_DATE": crt_datetime
                   }
    transister_ph = {"SENSOR": "TRANSISTOR_PH",
                     "SENSOR_MAKER": "SBE",
                     "SENSOR_MODEL": "SEAFET",
                     "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                     "ADD_DATE": crt_datetime
                     }
    fluorometer_cdom = {"SENSOR": "FLUOROMETER_CDOM",
                        "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                        "PREDEPLOYMENT_CALIB_COEFFICIENT": {"DARK_CDOM": None, "SCALE_CDOM": None},
                        "SENSOR_MAKER": "WETLABS",
                        "SENSOR_MODEL": "ECO_FLBBCD",
                        "ADD_DATE": crt_datetime
                        }
    bbp700 = {"SENSOR": "BACKSCATTERINGMETER_BBP700",
              "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
              "PREDEPLOYMENT_CALIB_COEFFICIENT": {"KHI": 1.097, "BETASW700": "calculated at 124 angularDeg", "DARK_BACKSCATTERING700": None, "SCALE_BACKSCATTERING700": None},
              "SENSOR_MAKER": "WETLABS",
              "SENSOR_MODEL": "ECO_FLBBCD",
              "ADD_DATE": crt_datetime
              }
    fluorometer_chla = {"SENSOR": "FLUOROMETER_CHLA",
                        "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                        "PREDEPLOYMENT_CALIB_COEFFICIENT": {"DARK_CHLA": None, "SCALE_CHLA": None},
                        "SENSOR_MAKER": "WETLABS",
                        "SENSOR_MODEL": "ECO_FLBBCD",
                        "ADD_DATE": crt_datetime
                        }
    nitrate = {"SENSOR": "SPECTROPHOTOMETER_NITRATE",
               "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
               "PREDEPLOYMENT_CALIB_COEFFICIENT": {"calibration file": None},
               "SENSOR_MAKER": "SATLANTIC",
               "SENSOR_MODEL": "SUNA_V2",
               "ADD_DATE": crt_datetime
               }
    
    ocr = {"SENSOR": "OCR",
               "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
               "PREDEPLOYMENT_CALIB_COEFFICIENT": {"calibration file": None},
               "SENSOR_MAKER": "SATLANTIC",
               "SENSOR_MODEL": "OCR-504",
               "ADD_DATE": crt_datetime
               }

    t_cal = {}
    cnd_cal = {}
    pres_cal = {}
    o2_cal = {}
    ph_calib = {}

    with open(checklog_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):

            mo = re.search(r'BGC SOLO (\d\d\d\d)', line)  # Serial Number
            if mo:
                FLOAT_SERIAL_NO = (mo.group(1))
            '''mo = re.search(r'NAVIS version\D*(\d*)', line)  # Rom Version
            if mo:
                deployment["ROM_VERSION"] = mo.group(1)

            mo = re.search(r'Modem ICCID: (\d*)', line)  # SIM
            if mo:
                deployment["SIM"] = mo.group(1)

            mo = re.search(r'Modem IMEI: (\d*)', line)  # IMEI
            if mo:
                print(mo.group(1))
                deployment["IMEI"] = mo.group(1)'''
            
    with open(ctd_cal_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            ########## SBE41cp #######################
            # sbe41cp serial number
            mo = re.search(r'SERIALNO=(\d\d\d\d\d)', line)
            if mo:
                ctd_temp["SENSOR_SERIAL_NO"] = mo.group(1)
                ctd_cndc["SENSOR_SERIAL_NO"] = mo.group(1)
                ctd_temp["SENSOR_MODEL"] = "SBE41CP"
                ctd_cndc["SENSOR_MODEL"] = "SBE41CP"

            # SBE41cp Temperature 1 cal date
            mo = re.search(r'TCALDATE=(\d\d-.*-\d\d)', line)
            if mo:
                ctd_temp["SENSOR_CALIB_DATE"] = datetime.strptime(
                    mo.group(1), '%d-%b-%y').strftime('%Y-%m-%d')
                

                next = ''.join(lines[i:i+5]).replace('\n', ' ')
                mo = re.search(r"TA0= ? ?(\S*)", next)
                if mo:
                    t_cal['TA0'] = float(mo.group(1))

                mo = re.search(r"TA1= ? ?(\S*)", next)
                if mo:
                    t_cal['TA1'] = float(mo.group(1))

                mo = re.search(r"TA2= ? ?(\S*)", next)
                if mo:
                    t_cal['TA2'] = float(mo.group(1))

                mo = re.search(r"TA3= ? ?(\S*)", next)
                if mo:
                    t_cal['TA3'] = float(mo.group(1))

            # Conductivity cal date
            mo = re.search(r'CCALDATE=(\S*)', line)
            if mo:
                ctd_cndc["SENSOR_CALIB_DATE"] = datetime.strptime(
                    mo.group(1), '%d-%b-%y').strftime('%Y-%m-%d')

                # CNDC calibraiton coefficients
                next = ''.join(lines[i:i+8]).replace('\n', ' ')
                mo = re.search(r"CG= ? ?(\S*)", next)
                if mo:
                    cnd_cal['G'] = float(mo.group(1))

                mo = re.search(r"CH= ? ?(\S*)", next)
                if mo:
                    cnd_cal['H'] = float(mo.group(1))

                mo = re.search(r"CI= ? ?(\S*)", next)
                if mo:
                    cnd_cal['I'] = float(mo.group(1))

                mo = re.search(r"CJ= ? ?(\S*)", next)
                if mo:
                    cnd_cal['J'] = float(mo.group(1))

                mo = re.search(r"WBOTC= ? ?(\S*)", next)
                if mo:
                    cnd_cal['WBOTC'] = float(mo.group(1))

                mo = re.search(r"CTCOR= ? ?(\S*)", next)
                if mo:
                    cnd_cal['CTCOR'] = float(mo.group(1))

                mo = re.search(r"CPCOR= ? ?(\S*)", next)
                if mo:
                    cnd_cal['CPCOR'] = float(mo.group(1))

            # Pressure serial number
            mo = re.search(r'PCALDATE=(\S*)', line)
            if mo:
                ctd_pres["SENSOR_CALIB_DATE"] = datetime.strptime(
                    mo.group(1), '%d-%b-%y').strftime('%Y-%m-%d')

                # Pressure calibration coefficients
                next = ''.join(lines[i:i+14]).replace('\n', ' ')
                mo = re.search(r"PA0= ? ?(\S*)", next)
                if mo:
                    pres_cal['PA0'] = float(mo.group(1))

                mo = re.search(r"PA1= ? ?(\S*)", next)
                if mo:
                    pres_cal['PA1'] = float(mo.group(1))

                mo = re.search(r"PA2= ? ?(\S*)", next)
                if mo:
                    pres_cal['PA2'] = float(mo.group(1))

                mo = re.search(r"PTCA0= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCA0'] = float(mo.group(1))

                mo = re.search(r"PTCA1= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCA1'] = float(mo.group(1))

                mo = re.search(r"PTCA2= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCA2'] = float(mo.group(1))

                mo = re.search(r"PTCB0= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCB0'] = float(mo.group(1))

                mo = re.search(r"PTCB1= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCB1'] = float(mo.group(1))

                mo = re.search(r"PTCB2= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTCB2'] = float(mo.group(1))

                mo = re.search(r"PTHA0= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTHA0'] = float(mo.group(1))

                mo = re.search(r"PTHA1= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTHA1'] = float(mo.group(1))

                mo = re.search(r"PTHA2= ? ?(\S*)", next)
                if mo:
                    pres_cal['PTHA2'] = float(mo.group(1))

                mo = re.search(r"POFFSET= ? ?(\S*)", next)
                if mo:
                    pres_cal['POFFSET'] = float(mo.group(1))


    with open(ph_cal_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            # pH serial number
            pH_mo = re.search(r'serial_number = "(\d*)', line)
            if pH_mo:
                transister_ph["SENSOR_SERIAL_NO"] = pH_mo.group(1)
            pH_mo = re.search(r'date = "(\S*)', line)
            if pH_mo:
                transister_ph["SENSOR_CALIB_DATE"] = datetime.strptime(
                    pH_mo.group(1), '%Y-%m-%d').strftime('%Y-%m-%d')
                
            mo = re.search(r'\bf0 = (\S*)',line)
            if mo:
                ph_calib['F0']= float(mo.group(1))
            mo = re.search(r'\bf1 = (\S*)',line)
            if mo:
                ph_calib['F1']= float(mo.group(1))
            mo = re.search(r'\bf2 = (\S*)',line)
            if mo:
                ph_calib['F2']= float(mo.group(1))
            mo = re.search(r'\bf3 = (\S*)',line)
            if mo:
                ph_calib['F3']= float(mo.group(1))
            mo = re.search(r'f4 = (\S*)',line)
            if mo:
                ph_calib['F4']= float(mo.group(1))
            mo = re.search(r'f5 = (\S*)',line)
            if mo:
                ph_calib['F5']= float(mo.group(1))
            mo = re.search(r'f6 = (\S*)',line)
            if mo:
                ph_calib['F6']= float(mo.group(1))
            mo = re.search(r'f7 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:
                    ph_calib['F7']= float(mo.group(1))
            mo = re.search(r'f8 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:                
                    ph_calib['F8']= float(mo.group(1))
            mo = re.search(r'f9 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:                
                    ph_calib['F9']= float(mo.group(1))
            mo = re.search(r'f10 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:                
                    ph_calib['F10']= float(mo.group(1))
            mo = re.search(r'f11 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:                
                    ph_calib['F11']= float(mo.group(1))
            mo = re.search(r'f12 = (\S*)',line)
            if mo:
                if float(mo.group(1)) == 0:
                    pass
                else:                
                    ph_calib['F12']= float(mo.group(1))
            mo = re.search(r'K0 = (\S*)',line)
            if mo:
                ph_calib['K0']= float(mo.group(1))
            mo = re.search(r'K2f0 = (\S*)',line)
            if mo:
                ph_calib['K2f0']= float(mo.group(1))
            mo = re.search(r'K2f1 = (\S*)',line)
            if mo:
                ph_calib['K2f1']= float(mo.group(1))
            mo = re.search(r'K2f2 = (\S*)',line)
            if mo:
                ph_calib['K2f2']= float(mo.group(1))
            mo = re.search(r'K2f3 = (\S*)',line)
            if mo:
                ph_calib['K2f3']= float(mo.group(1))





    with open(o2_cal_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            # DOXY serial number
            DOXY_mo = re.search(
                r'SERIALNO=(\S*)', line)
            if DOXY_mo:
                optode_doxy["SENSOR_SERIAL_NO"] = DOXY_mo.group(1)
            
            # DOXY model
            optode_doxy["SENSOR_MODEL"] = "SBE83_OPTODE"

            # DOXY cal date
            DOXY_caldate = re.search(
                r'OxygenCalDate=(\S*)', line)
            if DOXY_caldate:
                optode_doxy["SENSOR_CALIB_DATE"] = datetime.strptime(
                    DOXY_caldate.group(1), '%Y-%m-%d').strftime('%Y-%m-%d')
                # DOXY Coefficients
                next = ''.join(lines[i:i+14]).replace('\n', ' ')
                mo = re.search(r'A0=(\S*)', next)
                if mo:
                    o2_cal['A0'] = float(mo.group(1))

                mo = re.search(r'A1=(\S*)', next)
                if mo:
                    o2_cal['A1'] = float(mo.group(1))

                mo = re.search(r'A2=(\S*)', next)
                if mo:
                    o2_cal['A2'] = float(mo.group(1))

                mo = re.search(r'B0=(\S*)', next)
                if mo:
                    o2_cal['B0'] = float(mo.group(1))

                mo = re.search(r'B1=(\S*)', next)
                if mo:
                    o2_cal['B1'] = float(mo.group(1))

                mo = re.search(r'C0=(\S*)', next)
                if mo:
                    o2_cal['C0'] = float(mo.group(1))

                mo = re.search(r'C1=(\S*)', next)
                if mo:
                    o2_cal['C1'] = float(mo.group(1))

                mo = re.search(r'C2=(\S*)', next)
                if mo:
                    o2_cal['C2'] = float(mo.group(1))

                mo = re.search(r'E=(\S*)', next)
                if mo:
                    o2_cal['E'] = float(mo.group(1))

                mo = re.search(r'TA0=(\S*)', next)
                if mo:
                    o2_cal['TA0'] = float(mo.group(1))

                mo = re.search(r'TA1=(\S*)', next)
                if mo:
                    o2_cal['TA1'] = float(mo.group(1))

                mo = re.search(r'TA2=(\S*)', next)
                if mo:
                    o2_cal['TA2'] = float(mo.group(1))

                mo = re.search(r'TA3=(\S*)', next)
                if mo:
                    o2_cal['TA3'] = float(mo.group(1))

            # MCOMS serial number
            '''mo = re.search(r'MCOMS serial number: \[(\d*)\]', line)
            if mo:
                fluorometer_cdom["SENSOR_SERIAL_NO"] = mo.group(1)
                bbp700["SENSOR_SERIAL_NO"] = mo.group(1)
                fluorometer_chla["SENSOR_SERIAL_NO"] = mo.group(1)'''

            # Nitrate serial number
    with open(suna_cal_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            mo = re.search(
                r'SUNA (\d*) Cal', line)
            if mo:
                nitrate["SENSOR_SERIAL_NO"] = mo.group(1)
          

            '''# Battery voltage
            batt_mo = re.search(r'Battery \[\S* (\d*.\d*)', line)
            if batt_mo:
                print(batt_mo.group(1))
                deployment["BATTERY_VOLTAGE"] = batt_mo.group(1)'''

    # Decode SUNA .cal file
    suna_cal = decode_suna_cal(suna_cal_f)
    nitrate['PREDEPLOYMENT_CALIB_COEFFICIENT'].update(suna_cal)
    ctd_cndc["PREDEPLOYMENT_CALIB_COEFFICIENT"] = cnd_cal
    ctd_pres["PREDEPLOYMENT_CALIB_COEFFICIENT"] = pres_cal
    ctd_temp["PREDEPLOYMENT_CALIB_COEFFICIENT"] = t_cal
    optode_doxy['PREDEPLOYMENT_CALIB_COEFFICIENT'] = o2_cal
    try:
        transister_ph['PREDEPLOYMENT_CALIB_COEFFICIENT'] = ph_calib
    except:
        pass

    sensors = [ctd_cndc, ctd_pres, ctd_temp, optode_doxy, transister_ph,
               fluorometer_cdom, fluorometer_chla, bbp700, nitrate, ocr]


    #print(deployment)
    print(FLOAT_SERIAL_NO)
    print(sensors)

    if add_to_db:
        # Update deployment database
        try:
            db.update_deployment(FLOAT_SERIAL_NO, 'SOLO_BGC_MRV', deployment)
        except:
            print("Add Deployment first online")

        # Update or add sensors
        for sensor in sensors:
            try:
                db.update_sensor(FLOAT_SERIAL_NO, 'SOLO_BGC_MRV',
                                 sensor['SENSOR'], sensor)
            except:
                db.add_sensor(FLOAT_SERIAL_NO, 'SOLO_BGC_MRV', sensor)


if __name__ == "__main__":
    ctd_cal = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\4057\\sensor_cal\\CTD_DOXY\\21464.cal'
    suna_cal = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\4057\\sensor_cal\\SUNA\\SUNA_2476.cal'
    fn = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\4057\\checkout\\4057_full_bit_20250819.log'
    ph_cal = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\4057\\sensor_cal\\CTD_DOXY\\21464-20755 ISFET pH.cal'
    o2_cal = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\4057\\sensor_cal\\SBE83\\0238.cal'
    read_checklog(fn, suna_cal, ctd_cal,ph_cal, o2_cal, add_to_db=True)
