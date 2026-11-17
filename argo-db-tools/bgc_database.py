import requests
import json
import os
from dotenv import load_dotenv
print("Load ENV")
load_dotenv()
# Tools to interact with database


BASE_URL = "https://db.whoifloatgroup.org"
#BASE_URL = "http://127.0.0.1:8000"

TOKEN = os.environ.get("TOKEN")
headers = {'Authorization': TOKEN, 'Content-Type': 'application/json'}

def update_deployment(FLOAT_SERIAL_NO, PLATFORM_TYPE, data):
    response = requests.patch(BASE_URL+"/api/metadata", json=data, headers=headers,
                              params={"FLOAT_SERIAL_NO": FLOAT_SERIAL_NO, "PLATFORM_TYPE": PLATFORM_TYPE})

    if response.status_code == 200:
        print('Sucessfully updated deployment')
        return json.loads(response.content)
    raise Exception('ERROR: ', response.status_code)


def post_deployment(data):
    response = requests.post(BASE_URL+"/api/metadata",
                             json=data, headers=headers)

    if response.status_code == 201:
        #print('Sucessfully added deployment')
        return json.loads(response.content)
    raise Exception('ERROR: ', response.content)


def update_sensor(FLOAT_SERIAL_NO, PLATFORM_TYPE, SENSOR, data):
    print(headers)
    response = requests.patch(BASE_URL+"/api/sensors", json=data, headers=headers,
                              params={"FLOAT_SERIAL_NO": FLOAT_SERIAL_NO, "PLATFORM_TYPE": PLATFORM_TYPE, "SENSOR": SENSOR})

    if response.status_code == 200:
        print('Sucessfully updated sensor')
        return json.loads(response.content)
    raise Exception('ERROR: ', response.status_code)


def add_sensor(FLOAT_SERIAL_NO, PLATFORM_TYPE, data):

    response = requests.post(BASE_URL+"/api/sensors", json=data, headers=headers,
                             params={"FLOAT_SERIAL_NO": FLOAT_SERIAL_NO, "PLATFORM_TYPE": PLATFORM_TYPE})

    if response.status_code == 201:
        print('Sucessfully created sensor')
    else:
        print('ERROR: ', response.status_code)
        print(response.content)


def get_current_metadata(wmo):
    response = requests.get(
        BASE_URL+"/api/current_metadata/", params={"PLATFORM_NUMBER": wmo})

    if response.status_code == 200:
        print('Sucessfully got metadata')
        print(response.content)
    else:
        print('ERROR: ', response.status_code)
        print(response.content)


if __name__ == "__main__":

    # data = {
    #     "ADD_DATE": "2200-05-17T19:32:41Z",
    #     "SENSOR":"CTD_PRES"
    # }
    # try:
    #     res = update_sensor(1200, 'NAVIS_EBR', 'CTD_PRES', data)
    # except:
    #     res = add_sensor(1200,'NAVIS_EBR',data)

    data = {'WHOI_TAG': 9999}
    update_deployment(7539, 'S2A', data)