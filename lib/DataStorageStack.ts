import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';

export class DataStorageStack extends cdk.Stack {

  public bucket: s3.IBucket;

  /**
   *
   * @param scope
   * @param id
   * @param props
   */






  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here
    // S3 + Quicksight
    const bucket = new s3.Bucket(this, "targetBucket", {
      versioned: true,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: new kms.Key(this, "StorageKey", {
          description: `KMS key for s3`,
          enableKeyRotation: true,
          trustAccountIdentities: true,
      }),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
  });

    this.bucket = bucket;

  }
}