import boto3
from pytz import timezone
from datetime import datetime
import config

def record_requests():
    # Create CloudWatch client

    # print(config.get_instanceId())

    cloudwatch = boto3.client('cloudwatch')

    # Put custom metrics
    cloudwatch.put_metric_data(
        MetricData=[
            {
                'MetricName': 'HTTP_request',
                'Dimensions': [
                    {
                        'Name': 'INSTANCE_ID',
                        'Value': 'id'
                    },
                ],
                'Timestamp': datetime.now(timezone('Canada/Eastern')),
                'Unit': 'Count',
                'Value': 1.0
            },
        ],
        Namespace='SITE/TRAFFIC'
    )



