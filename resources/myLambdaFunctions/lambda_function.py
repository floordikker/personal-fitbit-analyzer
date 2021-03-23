import fitbit
import pandas as pd 
import datetime
import json
import requests
import gather_keys_oauth2 as Oauth2
import boto3
import os
import io

# clients & resources
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

# environmental variables
sourceBucket = os.environ['S3_SOURCE_BUCKET']                       ## Bucket with credentials for Fitbit API saved
targetBucket = os.environ['S3_DESTINATION_BUCKET']                  ## Bucket with data that is used for input in dashboard
fitbitCredentials = os.environ['FITBIT_CREDENTIALS_FILE']           ## Name of the credential file saved in sourceBucket

def getting_week_dates(startDate = None, endDate = None):
    """Helper function to get all the dates of last week, if startdates and endates are specified, those dates are used"""
    if startDate and endDate:
        weekDatesRaw = pd.date_range(start = startDate, end = endDate, freq = 'D')
        weekDates = [str(x).split(' ')[0] for x in weekDatesRaw]
    else:
        weekDatesRaw = pd.date_range(end = pd.to_datetime('today'), periods = 7, freq = 'D')
        weekDates = [str(x).split(' ')[0] for x in weekDatesRaw]
        startDate = weekDates[0]
        endDate = weekDates[6]    
    return weekDates, startDate, endDate


def read_data_from_S3_as_text(sourceBucket, fileKey):
    """Read text file with name fileKey from bucket with name sourceBucket and return as JSON"""
    s3Obj = s3.get_object(Bucket=sourceBucket, Key=fileKey)
    s3Data = s3Obj['Body'].read().decode('utf-8')
    jsonContent = json.loads(s3Data)
    return jsonContent


def read_data_from_S3_as_CSV(targetBucket, fileKey):
    """Read csv file with name fileKey from bucket with name targetBucket and return as pd.DataFrame"""
    obj = s3_resource.Object(targetBucket, fileKey)
    with io.BytesIO(obj.get()['Body'].read()) as myFile:
        df = pd.read_csv(myFile)
    return df


def write_data_to_S3(targetBucket, fileKey, df):
    """Write df to bucket with name targetBucket as csv with name fileKey"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    s3_resource.Object(targetBucket, fileKey).put(Body=csv_buffer.getvalue())


def read_process_and_write(targetBucket, fileKey, myRecords):
    """Read existing logs, concatenate new logs myRecords and safe with name fileKey in bucket targetBucket"""
    response = s3.list_objects(Bucket = targetBucket)
    if 'Contents' in response.keys():                                   ## bucket is not empty
        presentFiles = [x['Key'] for x in response['Contents']]
        if fileKey in presentFiles:
            existingData = read_data_from_S3_as_CSV(targetBucket, fileKey)
            myRecordsNew = pd.concat([existingData, myRecords], axis = 0)
            write_data_to_S3(targetBucket, fileKey, myRecordsNew)
        else:
            write_data_to_S3(targetBucket, fileKey, myRecords)
    else:
        write_data_to_S3(targetBucket, fileKey, myRecords)


def getting_sleep_data(myCredentials, startDate, endDate):
    """GET request for sleep data"""
    headers = {"Authorization" : "Bearer " + myCredentials["ACCES_TOKEN"]}
    http_request_get_test = "https://api.fitbit.com/1.2/user/-/sleep/date/" + startDate + '/' + endDate + '.json'
    response = requests.get(http_request_get_test, headers=headers)
    responseJson = response.json()
    return responseJson

def parsing_sleep_data(response, targetBucket, weekDates, endDate):
    """Parsing useful information from API Response and saving it to targetBucket"""
    mySleep = response['sleep']
    myKeys = ['dateOfSleep', 'minutesAfterWakeup', 'minutesAsleep', 'minutesAwake', 'minutesToFallAsleep', 'startTime', 'timeInBed', 'efficiency', 'duration', 'dateOfSleep']
    myRecords = pd.DataFrame()
    for i in range(len(weekDates)):
        try:                                            ## if for some reason data is missing for a record, we skip the day
            currentRecord = {}
            day = mySleep[i]
            for key in myKeys:
                currentRecord[key] = day[key]
            currentRecord['minutesDeepSleep'] = day['levels']['summary']['deep']['minutes']
            currentRecord['minutesLightSleep'] = day['levels']['summary']['light']['minutes']
            currentRecord['minutesRemSleep'] = day['levels']['summary']['rem']['minutes']
            currentRecord['minutesWakeSleep'] = day['levels']['summary']['wake']['minutes']
            myRecords = myRecords.append(currentRecord, ignore_index=True)
        except:
            continue
    return myRecords

def lambda_handler(event, context):
    variabelen = event
    weekDates, startDate, endDate = getting_week_dates('2021-02-01', '2021-03-20')
    myCredentials = read_data_from_S3_as_text(sourceBucket, fitbitCredentials)['CREDENTIALS']
    response = getting_sleep_data(myCredentials, startDate, endDate)
    mySleepRecords = parsing_sleep_data(response, targetBucket, weekDates, endDate)
    contents = read_process_and_write(targetBucket, 'mySleepData.csv', mySleepRecords)
    return {
        'statusCode': 200
    }
