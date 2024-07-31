# Author: Brian Fitzsimmons
# Date: 07-29-2024
# Description: This program is meant to act as a gateway from the WTEC gate to our
# Tandem model to be called. By setting up this gateway, we can create a buffer off the IOT network. 


import json
import os
import requests
import time

def read_secrets() -> dict:
    try:
        with open('secrets.json') as f:
            return json.load(f)
    except FileNotFoundError:
        print("secrets.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error decoding secrets.json file.")
        return {}



def fetch_data_from_source(url, secrets):
    """Fetch data from the source API."""
    try:
        response = requests.get(url, verify = False, auth=(secrets["user"], secrets["password"]))
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Return data as a JSON object
    except requests.RequestException as e:
        print(f"Error fetching data from source: {e}")
        return None
    
def motion_conversion(curr, prev):
    """Convert number to boolean for motion detection."""
    if curr != prev:
        return 1  # Motion detected
    return 0  # No motion
    
def push_data_to_tandem(data, url):
    """Push data to Autodesk Tandem Connect."""
    try:  
        response = requests.post(url, data=json.dumps(data))
        response.raise_for_status()  # Raise an error for bad status codes
        print("Data successfully pushed to Tandem Connect.")
    except requests.RequestException as e:
        print(f"Error pushing data to Tandem Connect: {e}")
def main():
    secrets = read_secrets()
    if not secrets:
        print("No secrets loaded. Exiting...")
        return
    
    source_urls = secrets.get("source_urls", [])
    tandem_urls = secrets.get("tandem_urls", [])

    if not source_urls or not tandem_urls:
        print("Source URLs or Tandem URLs are missing. Exiting...")
        return
   
    prev_motion = [None] * len(source_urls)
    

    while True:
         for i, (source_url, tandem_url) in enumerate(zip(secrets["source_urls"], secrets["tandem_urls"])):
            data = fetch_data_from_source(source_url, secrets)
            if data:
                #check if motion is the keyword
                curr_motion = data.get('sensorStats', {}).get('motion', {}).get('instant')

                if curr_motion is not None:
                    if prev_motion[i] is None:
                        prev_motion[i] = curr_motion

                    motion_detected = motion_conversion(curr_motion, prev_motion[i])
                    prev_motion[i] = curr_motion # update prev motion value

                    #prep data for push
                    sensor_stats = data.get('sensorStats', {})
                    datapush = {
                        'motion': motion_detected,
                        'power': sensor_stats.get('power', {}).get('instant'),
                        'ceilingTemperature': sensor_stats.get('ceilingTemperature', {}).get('instant'),
                        'roomTemperature': sensor_stats.get('roomTemperature', {}).get('instant'),
                        'illuminance': sensor_stats.get('illuminance', {}).get('instant'),
                        'brightness': sensor_stats.get('brightness', {}).get('instant'),
                        'humidity': sensor_stats.get('humidity', {}).get('instant'),
                        'pressure': sensor_stats.get('pressure', {}).get('instant'),
                        'indoorAirQuality': sensor_stats.get('indoorAirQuality', {}).get('instant'),
                        'co2': sensor_stats.get('co2', {}).get('instant'),
                        'voc': sensor_stats.get('voc', {}).get('instant')
                    }



                # Push data to Autodesk Tandem Connect
                    push_data_to_tandem(datapush, tandem_url)
                else:
                    print("No 'motion' parameter found")
            else: 
                print("No data fetched from source")

            time.sleep(30) #wait for 5 minutes to run again

if __name__ == "__main__":
    main()
