# My own fitbit dasbhoard on AWS QuickSight

This project contains code to set up a dashboard containing FitBit data and personal health data.
The goal of this project has been to provide more insight into long term correlations and see whether trends exists.

## Set up

The infrastructure is written in Typescript and the runtime code is written in Python. 
The infrastructure contains:
* S3 Bucket to host data needed to interact with the Fitbit data
* S3 Bucket for personal files and processed Fitbit data
* QuickSight dashboard
* Lambda function with run time code that is triggered each Monday at 09.00 pm

The health data is saved on my personal computer and upload to S3 (same bucket as processed Fitbit data) by means of a CRON job every week at 09.00 am. The script that executes this and my personal health records are saved in the folder scripts. 

## Version control

The code on the Main branch is the version of the project that is hosted on AWS on this moment.
The code on the Develop branch is tested code but is not necessarily live.
Feature branches are used to develop new features and when tested, it is merged to Develop

## To do:

* Error handling in lambda function. Notify if function fails. Also send a notification if lambda functions succeeds.
* Adding own health logs
* Building QuickSight Dashboard