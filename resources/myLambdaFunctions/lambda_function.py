import fitbit
import pandas as pd 
import datetime
import json
import requests
import gather_keys_oauth2 as Oauth2
import boto3
import os

#clients
s3 = boto3.client('s3')

# environmental variables
bucketName = os.environ['S3_BUCKET']
fitbitCredentials = os.environ['FITBIT_CREDENTIALS_FILE']

def getting_week_dates():
    """Helper function to get all the dates of last week"""
    weekDatesRaw = pd.date_range(end = pd.to_datetime('today'), periods = 7, freq = 'D')
    weekDates = [str(x).split(' ')[0] for x in weekDatesRaw]
    aWeekAgo = weekDates[0]
    today = weekDates[6]
    return weekDates, aWeekAgo, today

def read_data_from_S3(bucketName, fileKey):
    """Read file with name fileKey from bucket with name bucketName"""
    s3Obj = s3.get_object(Bucket=bucketName, Key=fileKey)
    s3Data = s3Obj['Body'].read().decode('utf-8')
    jsonContent = json.loads(s3Data)
    return jsonContent

def getting_sleep_data(myCredentials):
    """GET request for sleep data"""
    headers = {"Authorization" : "Bearer " + myCredentials["ACCES_TOKEN"]}
    weekDates, aWeekAgo, today = getting_week_dates()
    http_request_get_test = "https://api.fitbit.com/1.2/user/-/sleep/date/" + aWeekAgo + '/' + today + '.json'
    response = requests.get(http_request_get_test, headers=headers)
    responseJson = response.json()
    return responseJson

def lambda_handler(event, context):
    ## input variabelen
    variabelen = event
    # Fibit credentials
    myCredentials = read_data_from_S3(bucketName, fitbitCredentials)['CREDENTIALS']
    data = getting_sleep_data(myCredentials)
    return {
        'statusCode': 200,
        "testData": data
    }
