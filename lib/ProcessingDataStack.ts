import * as cdk from '@aws-cdk/core';
import * as lambda from '@aws-cdk/aws-lambda';
import * as events from '@aws-cdk/aws-events';
import * as targets from '@aws-cdk/aws-events-targets';
import * as s3 from '@aws-cdk/aws-s3'
import * as s3deploy from '@aws-cdk/aws-s3-deployment';


export class ProcessingDataStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
  
    // bucket with Fitbit credentials saved
    const sourceBucket = new s3.Bucket(this, "sourceBucket", {
      versioned: false,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new s3deploy.BucketDeployment(this, 'fitbitCredentials', {
      sources: [s3deploy.Source.asset('resources/fitbitCredentials')],
      destinationBucket: sourceBucket,
      retainOnDelete: false
    });



    const myLambda = new lambda.Function(this, 'Function', {
      runtime: lambda.Runtime.PYTHON_3_7,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset('resources/myLambdaFunctions', {
        bundling: {
          image: lambda.Runtime.PYTHON_3_7.bundlingDockerImage,
          command: [
            'bash',
            '-c', [
            'pip install numpy -t /asset-output',
            'pip install pandas -t /asset-output',
            'pip install fitbit -t /asset-output',
            'pip install datetime -t /asset-output',
            'pip install CherryPy -t /asset-output',
            'cp -au . /asset-output'].join(' && '),
          ],
        },
      }),
      environment: {
        'S3_BUCKET': sourceBucket.bucketName,
        'FITBIT_CREDENTIALS_FILE': 'credentials.txt'
      }
    });
    // Grand read access to bucket
    sourceBucket.grantRead(myLambda);


    // Defined schedule
    const mySchedule = events.Schedule.expression('cron(0 9 ? * 2#1 *)')
    // target
    const LambdaTarget = new targets.LambdaFunction(myLambda);
    // Al together
    const myRule = new events.Rule(this, 'RuleEveryWeek', {
      description : 'Rule to trigger lambda every month on Monday morning at 9 pm',
      schedule: mySchedule,
      targets: [LambdaTarget],

    });

  };
}





