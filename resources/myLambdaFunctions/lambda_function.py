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


def getting_data(myCredentials, url, startDate, endDate):
    """GET request for given url from startDate to endDate"""
    headers = {"Authorization" : "Bearer " + myCredentials["ACCES_TOKEN"]}
    http_request_get_test = url + startDate + '/' + endDate + '.json'
    response = requests.get(http_request_get_test, headers=headers)
    responseJson = response.json()
    return responseJson
    

def parsing_sleep_data(myCredentials, targetBucket, weekDates, startDate, endDate):
    """Parsing useful sleep information from API Response and saving it to targetBucket"""
    response = getting_data(myCredentials, "https://api.fitbit.com/1.2/user/-/sleep/date/" , startDate, endDate)
    mySleep = response['sleep']
    myKeys = ['minutesAfterWakeup', 'minutesAsleep', 'minutesAwake', 'minutesToFallAsleep', 'startTime', 'timeInBed', 'efficiency', 'duration', 'dateOfSleep']
    myRecords = pd.DataFrame()
    for i in range(len(weekDates)):
        try:                                            ## if for some reason data is missing for a record, we skip the day
            currentRecord = {}
            day = mySleep[i]
            for key in myKeys:
                currentRecord[key] = day[key]
            currentRecord['date'] = day['dateOfSleep']
            currentRecord['minutesDeepSleep'] = day['levels']['summary']['deep']['minutes']
            currentRecord['minutesLightSleep'] = day['levels']['summary']['light']['minutes']
            currentRecord['minutesRemSleep'] = day['levels']['summary']['rem']['minutes']
            currentRecord['minutesWakeSleep'] = day['levels']['summary']['wake']['minutes']
            myRecords = myRecords.append(currentRecord, ignore_index=True)
        except:
            continue
    read_process_and_write(targetBucket, 'mySleepData.csv', myRecords)
    return myRecords


def parsing_heart_rate_data(myCredentials, targetBucket, weekDates, startDate, endDate):
    """Parsing useful heart rate information from API Response and saving it to targetBucket"""
    response = getting_data(myCredentials, "https://api.fitbit.com/1.2/user/-/activities/heart/date/" , startDate, endDate)
    myHeartRate = response['activities-heart']
    myRecords = pd.DataFrame()
    for i in range(len(weekDates)):
        try:                                            ## if for some reason data is missing for a record, we skip the day
            currentRecord = {}
            currentRecord['date'] = myHeartRate[i]['dateTime']
            day = myHeartRate[i]['value']
            currentRecord['restingHeartRate'] = day['restingHeartRate']
            currentRecord['minutesOutOfRange'] = day['heartRateZones'][0]['minutes']
            currentRecord['caloriesOutOfRange'] = day['heartRateZones'][0]['caloriesOut']
            currentRecord['minutesFatBurn'] = day['heartRateZones'][1]['minutes']
            currentRecord['caloriesFatBurn'] = day['heartRateZones'][1]['caloriesOut']
            currentRecord['minutesCardio'] = day['heartRateZones'][2]['minutes']
            currentRecord['caloriesCardio'] = day['heartRateZones'][2]['caloriesOut']
            currentRecord['minutesPeak'] = day['heartRateZones'][3]['minutes']
            currentRecord['caloriesPeak'] = day['heartRateZones'][3]['caloriesOut']
            myRecords = myRecords.append(currentRecord, ignore_index=True)
        except:
            continue
    read_process_and_write(targetBucket, 'myHeartRateData.csv', myRecords)
    return myRecords


def parsing_activities_data(myCredentials, targetBucket, weekDates, startDate, endDate):
    """Parsing useful activities information from API Response and saving it to targetBucket"""
    """Activity API is build differently then the other APIs"""
    usefulInformation = ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 'elevation', 'minutesSedentary',
                        'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'activityCalories']
    myRecords = pd.DataFrame()
    myRecords['date'] = weekDates
    for key in usefulInformation:
        activityRecord = pd.DataFrame()
        baseUrl = "https://api.fitbit.com/1.2/user/-/activities/" + key + "/date/"
        response = getting_data(myCredentials, baseUrl , startDate, endDate)
        for i in range(len(weekDates)):
            try:
                currentRecord = {}
                jsonKey = 'activities-' + key
                myActivity = response[jsonKey][i]
                currentRecord[key] = myActivity['value']
                activityRecord = activityRecord.append(currentRecord, ignore_index=True)
            except:
                continue
        myRecords = pd.concat([myRecords, activityRecord], axis = 1)
    read_process_and_write(targetBucket, 'myActivitiesData.csv', myRecords)
    return myRecords
        

def lambda_handler(event, context):
    variabelen = event
    weekDates, startDate, endDate = getting_week_dates()
    myCredentials = read_data_from_S3_as_text(sourceBucket, fitbitCredentials)['CREDENTIALS']
    mySleepRecords = parsing_sleep_data(myCredentials, targetBucket, weekDates, startDate, endDate)
    myHeartRateRecords = parsing_heart_rate_data(myCredentials, targetBucket, weekDates, startDate, endDate)
    myActivityRecords = parsing_activities_data(myCredentials, targetBucket, weekDates, startDate, endDate)
    return {
        'statusCode': 200
    }
