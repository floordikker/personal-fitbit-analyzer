#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { ProcessingDataStack } from '../lib/ProcessingDataStack';
import { DataStorageStack } from '../lib/DataStorageStack';


const app = new cdk.App();

const dataStorageStack = new DataStorageStack(
    app,
    "DataStorageStack",
    {
        stackName: `data-storage-stack`,
    },
);

const processingDataStack = new ProcessingDataStack(
    app,
    "ProcessingDataStack",
    {
        stackName: `data-processing-stack`,
        bucket: dataStorageStack.bucket
        
    },
);


