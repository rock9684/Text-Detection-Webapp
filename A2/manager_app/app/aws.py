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
            new_instance_state = self.ec2.describe_instance_status(InstanceIds=[new_instance_id])
            
            if len(new_instance_state['InstanceStatuses']) < 1:
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

    def grow_worker_by_ratio(self, ratio):
        """
        add one instance into the self.TargetGroupArn
        :return: msg: str
        """
        target_instances = self.get_valid_target_instances()
        register_targets_num = int(len(target_instances) * (ratio-1))
        response_list = []
        if register_targets_num <= 0:
            return "Invalid ratio"
        if len(target_instances) < 1:
            return "You have no target instance in your group yet."

        for i in range(register_targets_num):
            response_list.append(self.grow_worker_by_one())
        return response_list

    def shrink_worker_by_one(self):
        """
        shrink one instance into the self.TargetGroupArn
        :return: msg: str
        """
        target_instances_id = self.get_valid_target_instances()
        flag, msg = True, ''
        if len(target_instances_id) > 1:
            unregister_instance_id = target_instances_id[0]

            # unregister instance from target group
            response1 = self.elb.deregister_targets(
                TargetGroupArn=self.TargetGroupArn,
                Targets=[
                    {
                        'Id': unregister_instance_id
                    },
                ]
            )
            status1 = -1
            if response1 and 'ResponseMetadata' in response1 and \
                    'HTTPStatusCode' in response1['ResponseMetadata']:
                status1 = response1['ResponseMetadata']['HTTPStatusCode']

            if int(status1) == 200:
                #stop instance
                status2 = -1
                response2 = self.ec2.stop_instances(
                    InstanceIds=[
                        unregister_instance_id,
                    ],
                    Hibernate=False,
                    Force=False
                )
                if response2 and 'ResponseMetadata' in response2 and \
                        'HTTPStatusCode' in response2['ResponseMetadata']:
                    status2 = response2['ResponseMetadata']['HTTPStatusCode']
                if int(status2) != 200:
                    flag = False
                    msg = "Unable to stop the unregistered instance"
            else:
                flag = False
                msg = "Unable to unregister from target group"

        else:
            flag = False
            msg = "No workers to unregister"

        return [flag, msg]
            
    def shrink_worker_by_ratio(self, ratio):
        """
        shrink one instance into the self.TargetGroupArn
        :return: msg: str
        """
        target_instances_id = self.get_valid_target_instances()
        response_list = []
        if ratio < 1:
            return [False, "Ratio should be more than 1", response_list]
        elif len(target_instances_id) < 1:
            return [False, "Target instance group is already null", response_list]
        else:
            shrink_targets_num = len(target_instances_id) - ceil(len(target_instances_id) * round(1/ratio, 2))
            for i in range(shrink_targets_num):
                response_list.append(self.shrink_worker_by_one())
        
        return [True, "Success", response_list]


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
        print(instance_ids)
        # 3 seconds for all workers to finish ongoing tasks
        time.sleep(3)
        self.ec2.terminate_instances(InstanceIds=instance_ids)