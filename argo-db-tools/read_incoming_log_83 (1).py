from ctypes.wintypes import FLOAT
import re
from datetime import datetime, timedelta
import bgc_database as db
from decode_suna_cal import decode_suna_cal


def read_checklog(checklog_f, suna_cal_f, add_to_db=False):
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
                     "PREDEPLOYMENT_CALIB_COEFFICIENT": {"F0": None, "F1": None, "F2": None, "F3": None, "F4": None, "F5": None, "F6": None, "K0": None, "K2": None},
                     "ADD_DATE": crt_datetime
                     }
    fluorometer_cdom = {"SENSOR": "FLUOROMETER_CDOM",
                        "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                        "PREDEPLOYMENT_CALIB_COEFFICIENT": {"DARK_CDOM": None, "SCALE_CDOM": None},
                        "SENSOR_MAKER": "WETLABS",
                        "SENSOR_MODEL": "MCOMS_FLBBCD",
                        "ADD_DATE": crt_datetime
                        }
    bbp700 = {"SENSOR": "BACKSCATTERINGMETER_BBP700",
              "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
              "PREDEPLOYMENT_CALIB_COEFFICIENT": {"KHI": 1.097, "BETASW700": "calculated at 124 angularDeg", "DARK_BACKSCATTERING700": None, "SCALE_BACKSCATTERING700": None},
              "SENSOR_MAKER": "WETLABS",
              "SENSOR_MODEL": "MCOMS_FLBBCD",
              "ADD_DATE": crt_datetime
              }
    fluorometer_chla = {"SENSOR": "FLUOROMETER_CHLA",
                        "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
                        "PREDEPLOYMENT_CALIB_COEFFICIENT": {"DARK_CHLA": None, "SCALE_CHLA": None},
                        "SENSOR_MAKER": "WETLABS",
                        "SENSOR_MODEL": "MCOMS_FLBBCD",
                        "ADD_DATE": crt_datetime
                        }
    nitrate = {"SENSOR": "SPECTROPHOTOMETER_NITRATE",
               "PREDEPLOYMENT_CALIB_EQUATION": {"eq1": None},
               "PREDEPLOYMENT_CALIB_COEFFICIENT": {"calibration file": None},
               "SENSOR_MAKER": "SATLANTIC",
               "SENSOR_MODEL": "SUNA_V2",
               "ADD_DATE": crt_datetime
               }

    t_cal = {}
    cnd_cal = {}
    pres_cal = {}

    with open(checklog_f, 'r', encoding='ANSI') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):

            mo = re.search(r'Float serial number:\s(\d*)', line)  # Serial Number
            if mo:
                FLOAT_SERIAL_NO = (mo.group(1))
            mo = re.search(r'NAVIS version\D*(\d*)', line)  # Rom Version
            if mo:
                deployment["ROM_VERSION"] = mo.group(1)

            mo = re.search(r'Modem ICCID: (\d*)', line)  # SIM
            if mo:
                deployment["SIM"] = mo.group(1)

            mo = re.search(r'Modem IMEI: (\d*)', line)  # IMEI
            if mo:
                print(mo.group(1))
                deployment["IMEI"] = mo.group(1)
            

            ########## SBE41cp #######################
            # sbe41cp serial number
            mo = re.search(r'Sbe41cpLogCal\(\)', line)
            if mo:
                mo2 = re.search(
                    r'SBE\s41N\sV\s(\d\.\d\.\d)\s*SERIAL\sNO\.\s*(\d*)', line)
                if mo2:
                    ctd_temp["SENSOR_SERIAL_NO"] = mo2.group(2)
                    ctd_cndc["SENSOR_SERIAL_NO"] = mo2.group(2)
                    ctd_temp["SENSOR_MODEL"] = "SBE41CP_V"+mo2.group(1)
                    ctd_cndc["SENSOR_MODEL"] = "SBE41CP_V"+mo2.group(1)

            # SBE41cp Temperature 1 cal date
            mo = re.search(r'Sbe41cpLogCal\(\)\s*temperature_1:\s*(\S*)', line)
            if mo:
                ctd_temp["SENSOR_CALIB_DATE"] = datetime.strptime(
                    mo.group(1), '%d-%b-%y').strftime('%Y-%m-%d')
                

                next = ''.join(lines[i:i+5]).replace('\n', ' ')
                mo = re.search(r"TA0 = (\S*)", next)
                if mo:
                    t_cal['TA0'] = float(mo.group(1))

                mo = re.search(r"TA1 = (\S*)", next)
                if mo:
                    t_cal['TA1'] = float(mo.group(1))

                mo = re.search(r"TA2 = (\S*)", next)
                if mo:
                    t_cal['TA2'] = float(mo.group(1))

                mo = re.search(r"TA3 = (\S*)", next)
                if mo:
                    t_cal['TA3'] = float(mo.group(1))

            # Conductivity cal date
            mo = re.search(r'Sbe41cpLogCal\(\)\s*conductivity:\s*(\S*)', line)
            if mo:
                ctd_cndc["SENSOR_CALIB_DATE"] = datetime.strptime(
                    mo.group(1), '%d-%b-%y').strftime('%Y-%m-%d')

                # CNDC calibraiton coefficients
                next = ''.join(lines[i:i+8]).replace('\n', ' ')
                mo = re.search(r"G = (\S*)", next)
                if mo:
                    cnd_cal['G'] = float(mo.group(1))

                mo = re.search(r"H = (\S*)", next)
                if mo:
                    cnd_cal['H'] = float(mo.group(1))

                mo = re.search(r"I = (\S*)", next)
                if mo:
                    cnd_cal['I'] = float(mo.group(1))

                mo = re.search(r"J = (\S*)", next)
                if mo:
                    cnd_cal['J'] = float(mo.group(1))

                mo = re.search(r"WBOTC = (\S*)", next)
                if mo:
                    cnd_cal['WBOTC'] = float(mo.group(1))

                mo = re.search(r"CTCOR = (\S*)", next)
                if mo:
                    cnd_cal['CTCOR'] = float(mo.group(1))

                mo = re.search(r"CPCOR = (\S*)", next)
                if mo:
                    cnd_cal['CPCOR'] = float(mo.group(1))

            # Pressure serial number
            mo = re.search(
                r'Sbe41cpLogCal\(\)\s*pressure\sS/N\s*=\s*(\d*)', line)
            if mo:
                ctd_pres["SENSOR_SERIAL_NO"] = mo.group(1)

                mo2 = re.search(r'(\S*)\s*$', line)  # cal date
                if mo2:
                    ctd_pres["SENSOR_CALIB_DATE"] = datetime.strptime(
                        mo2.group(1), '%d-%b-%y').strftime('%Y-%m-%d')

                # Pressure calibration coefficients
                next = ''.join(lines[i:i+14]).replace('\n', ' ')
                mo = re.search(r"PA0 = (\S*)", next)
                if mo:
                    pres_cal['PA0'] = float(mo.group(1))

                mo = re.search(r"PA1 = (\S*)", next)
                if mo:
                    pres_cal['PA1'] = float(mo.group(1))

                mo = re.search(r"PA2 = (\S*)", next)
                if mo:
                    pres_cal['PA2'] = float(mo.group(1))

                mo = re.search(r"PTCA0 = (\S*)", next)
                if mo:
                    pres_cal['PTCA0'] = float(mo.group(1))

                mo = re.search(r"PTCA1 = (\S*)", next)
                if mo:
                    pres_cal['PTCA1'] = float(mo.group(1))

                mo = re.search(r"PTCA2 = (\S*)", next)
                if mo:
                    pres_cal['PTCA2'] = float(mo.group(1))

                mo = re.search(r"PTCB0 = (\S*)", next)
                if mo:
                    pres_cal['PTCB0'] = float(mo.group(1))

                mo = re.search(r"PTCB1 = (\S*)", next)
                if mo:
                    pres_cal['PTCB1'] = float(mo.group(1))

                mo = re.search(r"PTCB2 = (\S*)", next)
                if mo:
                    pres_cal['PTCB2'] = float(mo.group(1))

                mo = re.search(r"PTHA0 = (\S*)", next)
                if mo:
                    pres_cal['PTHA0'] = float(mo.group(1))

                mo = re.search(r"PTHA1 = (\S*)", next)
                if mo:
                    pres_cal['PTHA1'] = float(mo.group(1))

                mo = re.search(r"PTHA2 = (\S*)", next)
                if mo:
                    pres_cal['PTHA2'] = float(mo.group(1))

                mo = re.search(r"POFFSET = (\S*)", next)
                if mo:
                    pres_cal['POFFSET'] = float(mo.group(1))

            # pH serial number
            pH_mo = re.search(r'pH\sserial\snumber:\s\[(\d*-\d*)', line)
            if pH_mo:
                transister_ph["SENSOR_SERIAL_NO"] = pH_mo.group(1)

            # DOXY serial number
            DOXY_mo = re.search(
                r'O2SensLogConfig\(\)     Serial#\D*(\d*)', line)
            if DOXY_mo:
                optode_doxy["SENSOR_SERIAL_NO"] = DOXY_mo.group(1)

            # DOXY cal date
            DOXY_caldate = re.search(
                r'O2SensLogConfig\(\)\s*Caldate\s*=\s*(\d*)', line)
            if DOXY_caldate:
                base_d = datetime(2000, 1, 1, 0, 0)
                add_d = timedelta(days=int(DOXY_caldate.group(1)))
                optode_doxy["SENSOR_CALIB_DATE"] = (
                    base_d + add_d).strftime('%Y-%m-%d')

            # DOXY model
            mo = re.search(
                r'O2SensLogConfig\(\)\s*Firmware\sRev\s*=\s*(\d*\.\d*\.\d*)', line)
            if mo:
                optode_doxy["SENSOR_MODEL"] = "SBE63_V"+mo.group(1)

            # DOXY Coefficients
            mo = re.search(r'O2SensLogCoef\(\)\s*A0\s*=\s*(.*)', line)
            if mo:
                A0 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*A1\s*=\s*(.*)', line)
            if mo:
                A1 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*A2\s*=\s*(.*)', line)
            if mo:
                A2 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*B0\s*=\s*(.*)', line)
            if mo:
                B0 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*B1\s*=\s*(.*)', line)
            if mo:
                B1 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*C0\s*=\s*(.*)', line)
            if mo:
                C0 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*C1\s*=\s*(.*)', line)
            if mo:
                C1 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*C2\s*=\s*(.*)', line)
            if mo:
                C2 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*E\s*=\s*(.*)', line)
            if mo:
                E = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*TA0\s*=\s*(.*)', line)
            if mo:
                TA0 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*TA1\s*=\s*(.*)', line)
            if mo:
                TA1 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*TA2\s*=\s*(.*)', line)
            if mo:
                TA2 = float(mo.group(1).strip())

            mo = re.search(r'O2SensLogCoef\(\)\s*TA3\s*=\s*(.*)', line)
            if mo:
                TA3 = float(mo.group(1).strip())

            # MCOMS serial number
            mo = re.search(r'MCOMS serial number: \[(\d*)\]', line)
            if mo:
                fluorometer_cdom["SENSOR_SERIAL_NO"] = mo.group(1)
                bbp700["SENSOR_SERIAL_NO"] = mo.group(1)
                fluorometer_chla["SENSOR_SERIAL_NO"] = mo.group(1)

            # Nitrate serial number
            mo = re.search(
                r'IsusConfigLog\(\) *H, SUNA Serial *Number , SN:(\d*)', line)
            if mo:
                nitrate["SENSOR_SERIAL_NO"] = mo.group(1)
            # Nitate calibration file
            mo = re.search(r'H, Calibration *File , (\S*)', line)
            if mo:
                nitrate['PREDEPLOYMENT_CALIB_COEFFICIENT'] = {
                    "calibration file": mo.group(1)}

            # Battery voltage
            batt_mo = re.search(r'Battery \[\S* (\d*.\d*)', line)
            if batt_mo:
                print(batt_mo.group(1))
                deployment["BATTERY_VOLTAGE"] = batt_mo.group(1)

    # Decode SUNA .cal file
    suna_cal = decode_suna_cal(suna_cal_f)
    nitrate['PREDEPLOYMENT_CALIB_COEFFICIENT'].update(suna_cal)
    # print(nitrate['PREDEPLOYMENT_CALIB_COEFFICIENT'])

    optode_doxy["PREDEPLOYMENT_CALIB_COEFFICIENT"] = {"A0": A0, "A1": A1, "A2": A2, "B0": B0, "B1": B1, "C0": C0,
                                                      "C1": C1, "C2": C2, "E": E, "TA0": TA0, "TA1": TA1, "TA2": TA2, "TA3": TA3}

    ctd_cndc["PREDEPLOYMENT_CALIB_COEFFICIENT"] = cnd_cal
    ctd_pres["PREDEPLOYMENT_CALIB_COEFFICIENT"] = pres_cal
    ctd_temp["PREDEPLOYMENT_CALIB_COEFFICIENT"] = t_cal

    sensors = [ctd_cndc, ctd_pres, ctd_temp, optode_doxy, transister_ph,
               fluorometer_cdom, fluorometer_chla, bbp700, nitrate]


    #print(deployment)
    print(FLOAT_SERIAL_NO)
    print(sensors)

    if add_to_db:
        # Update deployment database
        try:
            db.update_deployment(FLOAT_SERIAL_NO, 'NAVIS_EBR', deployment)
        except:
            print("Add Deployment first online")

        # Update or add sensors
        for sensor in sensors:
            try:
                db.update_sensor(FLOAT_SERIAL_NO, 'NAVIS_EBR',
                                 sensor['SENSOR'], sensor)
            except:
                db.add_sensor(FLOAT_SERIAL_NO, 'NAVIS_EBR', sensor)


if __name__ == "__main__":
    suna_cal = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\1585\sensor_cal\SUNA\\Calibration\SNA2192E.cal'
    fn = r'G:\Shared drives\WHOI Argo\BGC\\Floats\\1585\\checkout\\F1585_incoming_20231001.log'
    read_checklog(fn, suna_cal, add_to_db=True)
