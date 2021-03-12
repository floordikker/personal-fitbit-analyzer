#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { ProcessingDataStack } from '../lib/ProcessingDataStack';
import {baseEnv} from '../lib/_config';

const app = new cdk.App();

const shared = new ProcessingDataStack(
    app,
    "ProcessingDataStack",
    {
        ...baseEnv
    },
);