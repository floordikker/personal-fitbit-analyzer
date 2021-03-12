import { expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import * as FitbitInfra from '../lib/ProcessingDataStack';

test('Empty Stack', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new FitbitInfra.ProcessingDataStack(app, 'MyTestStack');
    // THEN
    expectCDK(stack).to(matchTemplate({
      "Resources": {}
    }, MatchStyle.EXACT))
});
