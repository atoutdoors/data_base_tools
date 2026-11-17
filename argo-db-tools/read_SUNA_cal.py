import pandas as pd
import json
import re
import pprint
from bgc_database import update_sensor

des = []
descal = {}
cal = []
other = []

with open("SNA1396B.CAL") as f:
    lines = f.readlines()
    for line in lines:
        if re.match("^H,\w*_",line): #Cal info in header
            mo = re.match("^H,(\w*_\S*)\s*(\d*\.?\d*)",line)
            print(mo.groups())
            if mo.group(2) == '':
                descal[mo.group(1)] = None
            else:
                descal[mo.group(1)] = float(mo.group(2))
        elif line[0]=='H': #All other header
            des.append(line.strip()[2:])
        elif line[0]=='E': #Cal
            cal.append(line.strip().split(','))
        else:
            other.append(line)

calibration = pd.DataFrame(cal, columns=['Linetype','Wavelength','NO3','SWA','TSWA','Reference'])
other = pd.DataFrame(other)

#Check if file format has changed
if len(other)>0:
    raise Exception("Cal sheet has changed, other line types")

if des[-1]!='Wavelength,NO3,SWA,TSWA,Reference':
    raise Exception("Cal sheet has changed, different cal columns")

data = {
    "PREDEPLOYMENT_CALIB_COEFFICIENT": {
        "header": des,
        "PATH_LENGHT":descal['PATH_LENGTH'],
        "INT_PERIOD":descal['INT_PERIOD'],
        "CONC_CAL_NO3":descal['CONC_CAL_NO3'],
        "CONC_CAL_SWA":descal['CONC_CAL_SWA'],
        "T_S_CORRECTABLE":descal['T_S_CORRECTABLE'],
        "T_CAL":descal["T_CAL"],
        "T_CAL_SWA":descal["T_CAL_SWA"],
        "Wavelength":calibration["Wavelength"].to_list(),
        "NO3":calibration["NO3"].to_list(),
        "SWA":calibration["SWA"].to_list(),
        "TSWA":calibration["TSWA"].to_list(),
        "Reference":calibration["Reference"].to_list()
        }
}

first_line = des[0]
sn = first_line.split(' ')[1]

pp = pprint.PrettyPrinter(compact=True)
pp.pprint(data)
#Send to database
update_sensor(sn, data)