import fitbit
import pandas as pd 
import datetime
import json
import requests
import gather_keys_oauth2 as Oauth2
import boto3
import os
import io

#clients
s3 = boto3.client('s3')

# environmental variables
sourceBucket = os.environ['S3_SOURCE_BUCKET']
targetBucket = os.environ['S3_DESTINATION_BUCKET']
fitbitCredentials = os.environ['FITBIT_CREDENTIALS_FILE']

def getting_week_dates():
    """Helper function to get all the dates of last week"""
    weekDatesRaw = pd.date_range(end = pd.to_datetime('today'), periods = 7, freq = 'D')
    weekDates = [str(x).split(' ')[0] for x in weekDatesRaw]
    aWeekAgo = weekDates[0]
    today = weekDates[6]
    return weekDates, aWeekAgo, today

def read_data_from_S3(sourceBucket, fileKey):
    """Read file with name fileKey from bucket with name sourceBucket"""
    s3Obj = s3.get_object(Bucket=sourceBucket, Key=fileKey)
    s3Data = s3Obj['Body'].read().decode('utf-8')
    jsonContent = json.loads(s3Data)
    return jsonContent

def write_data_to_S3(targetBucket, fileKey, df):
    """Write df to bucket with name targetBucket as csv with name fileKey"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3')
    s3_resource.Object(targetBucket, fileKey).put(Body=csv_buffer.getvalue())

def getting_sleep_data(myCredentials, aWeekAgo, today):
    """GET request for sleep data"""
    headers = {"Authorization" : "Bearer " + myCredentials["ACCES_TOKEN"]}
    http_request_get_test = "https://api.fitbit.com/1.2/user/-/sleep/date/" + aWeekAgo + '/' + today + '.json'
    response = requests.get(http_request_get_test, headers=headers)
    responseJson = response.json()
    return responseJson

def parsing_sleep_data(response, targetBucket, weekDates, today):
    """Parsing useful information from API Response and saving it to targetBucket"""
    mySleep = response['sleep']
    myKeys = ['dateOfSleep', 'minutesAfterWakeup', 'minutesAsleep', 'minutesAwake', 'minutesToFallAsleep', 'startTime', 'timeInBed', 'efficiency', 'duration', 'dateOfSleep']
    myRecords = pd.DataFrame()
    for i in range(len(weekDates)):
        currentRecord = {}
        day = mySleep[i]
        for key in myKeys:
            currentRecord[key] = day[key]
        currentRecord['minutesDeepSleep'] = day['levels']['summary']['deep']['minutes']
        currentRecord['minutesLightSleep'] = day['levels']['summary']['light']['minutes']
        currentRecord['minutesRemSleep'] = day['levels']['summary']['rem']['minutes']
        currentRecord['minutesWakeSleep'] = day['levels']['summary']['wake']['minutes']
        myRecords = myRecords.append(currentRecord, ignore_index=True)
    write_data_to_S3(targetBucket, 'sleep_data_' + today + '.csv', myRecords)
    return pd.DataFrame.to_dict(myRecords)

def lambda_handler(event, context):
    ## input variabelen
    variabelen = event
    # Fibit credentials
    weekDates, aWeekAgo, today = getting_week_dates()
    myCredentials = read_data_from_S3(sourceBucket, fitbitCredentials)['CREDENTIALS']
    response = getting_sleep_data(myCredentials, aWeekAgo, today)
    records = parsing_sleep_data(response, targetBucket, weekDates, today)
    return {
        'statusCode': 200,
        "testData": records
    }
