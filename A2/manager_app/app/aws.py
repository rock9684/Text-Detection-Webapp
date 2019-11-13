import boto3
import json
from math import ceil
import logging
from botocore.exceptions import ClientError
from operator import itemgetter
import time

class AwsClient:
    def __init__(self, access_key_id, secrete_key, region, template_id, target_arn, elb_dns):
        self.ec2 = boto3.client('ec2',
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secrete_key,
            region_name = region)
        self.elb = boto3.client('elbv2',
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secrete_key,
            region_name = region)
        self.s3 = boto3.client('s3', 
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secrete_key,
            region_name = region)
        self.cloudwatch = boto3.client('cloudwatch',
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secrete_key,
            region_name = region)
        self.template = template_id
        self.bucket = 'ece1779-bucket'
        self.target_group_arn = target_arn
        self.elb_dns = elb_dns

    def create_ec2_instance(self):
        response = self.ec2.run_instances(
            MaxCount = 1,
            MinCount = 1,
            LaunchTemplate = {'LaunchTemplateId': self.template})
        return response['Instances'][0]

    # if the instances in the target group are stopped, then the state is unused,
    # and the instances still stay in the target group.
    def get_target_instances(self):
        response = self.elb.describe_target_health(TargetGroupArn = self.target_group_arn)
        instance_list = []
        for instance in response['TargetHealthDescriptions']:
            instance_list.append({
                'id': instance['Target']['Id'],
                'port': instance['Target']['Port'],
                'state': instance['TargetHealth']['State']
                })
        return instance_list

    def grow_worker_by_one(self):
        response = self.create_ec2_instance()
        new_instance_id = response['InstanceId']

        # make sure the new instance is created
        while True:
            try:
                new_instance_state = self.ec2.describe_instance_status(InstanceIds=[new_instance_id])
            except Exception:
                continue
            
            if len(new_instance_state['InstanceStatuses']) < 1:
                time.sleep(1)
            elif new_instance_state['InstanceStatuses'][0]['InstanceState']['Name'] != 'running':
                time.sleep(1)
            else:
                break

        # register it
        register_response = self.elb.register_targets(
            TargetGroupArn = self.target_group_arn,
            Targets=[
                {
                    'Id': new_instance_id,
                    'Port': 5000
                },
            ]
        )

        if 'ResponseMetadata' in register_response:
            return register_response['ResponseMetadata']['HTTPStatusCode']
        else:
            return -1

    def shrink_worker_by_one(self):
        # terminate one worker
        target_instances = self.get_target_instances()
        instance_ids = []
        for instance in target_instances:
            instance_ids.append(instance['id'])
        # 3 seconds for it to finish ongoing tasks
        time.sleep(3)
        if len(instance_ids) != 0:
            self.ec2.terminate_instances(InstanceIds=[instance_ids[0]])
            return None

        return -1

    def grow_worker_by_some(self, new_instance_num):
        status_list = []
        for __ in range(new_instance_num):
            status_list.append(self.grow_worker_by_one())
        return status_list
            
    def shrink_worker_by_some(self, cut_instance_num):
        target_instances = self.get_target_instances()
        instance_ids = []
        for instance in target_instances:
            instance_ids.append(instance['id'])

        if len(instance_ids) >= (cut_instance_num + 1):
            instance_ids_to_cut = []
            for i in range(cut_instance_num):
                instance_ids_to_cut.append(instance_ids[i])
            time.sleep(3)
            self.ec2.terminate_instances(InstanceIds=instance_ids_to_cut)
            return None

        return -1


    def get_cpu_utilization(self, instance_id, start_time, end_time, period):
        response = self.cloudwatch.get_metric_statistics(
            Period = period,
            StartTime = start_time,
            EndTime = end_time,
            MetricName = 'CPUUtilization',
            Namespace = 'AWS/EC2',
            Statistics = ['Average'],
            Dimensions = [{'Name': 'InstanceId', 'Value': instance_id}]
        )

        cpu_stats = []

        if 'Datapoints' in response:
            for point in response['Datapoints']:
                hour = point['Timestamp'].hour
                minute = point['Timestamp'].minute
                time = hour + minute/60
                cpu_stats.append([time,point['Average']])
            cpu_stats = sorted(cpu_stats, key=itemgetter(0))

        return cpu_stats

    def get_http_request_rate(self, instance_id, start_time, end_time, period, unit):
        response = self.cloudwatch.get_metric_statistics(
            Period = period,
            StartTime = start_time,
            EndTime = end_time,
            MetricName = 'HTTP_request',
            Namespace = 'SITE/TRAFFIC', 
            Statistics = ['Sum'],
            Dimensions = [{'Name': 'INSTANCE_ID', 'Value': instance_id}],
            Unit = unit
        )

        http_stats = []

        if 'Datapoints' in response:
            for point in response['Datapoints']:
                hour = point['Timestamp'].hour
                minute = point['Timestamp'].minute
                time = hour + minute/60
                http_stats.append([time,point['Sum']])
            http_stats = sorted(http_stats, key=itemgetter(0))

        return http_stats

    def s3_clear(self):
        response = self.s3.list_objects(Bucket=self.bucket)
        if 'Contents' in response:
            for key in response['Contents']:
                self.s3.delete_object(
                    Bucket = self.bucket,
                    Key = key['Key']
                    )

    def terminate_all_workers(self):
        # terminate all workers
        target_instances = self.get_target_instances()
        instance_ids = []
        for instance in target_instances:
            instance_ids.append(instance['id'])
        # 3 seconds for all workers to finish ongoing tasks
        time.sleep(3)
        if len(instance_ids) != 0:
            self.ec2.terminate_instances(InstanceIds=instance_ids)






