import boto3
from datetime import datetime
from app import webapp, cw_client

def record_requests():
    # Put custom metrics
    cw_client.put_metric_data(
        MetricData=[
            {
                'MetricName': 'HTTP_request',
                'Dimensions': [
                    {
                        'Name': 'INSTANCE_ID',
                        'Value': webapp.config['INSTANCE_ID']
                    },
                ],
                'Timestamp': datetime.utcnow(),
                'Unit': 'Count',
                'Value': 1.0
            },
        ],
        Namespace='SITE/TRAFFIC'
    )



