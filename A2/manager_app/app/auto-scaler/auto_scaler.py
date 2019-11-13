import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append('../../')
sys.path.append(dir_path)
import time
from datetime import datetime, timedelta
from config import Config
from app.aws import AwsClient
import csv
import logging

def cpu_utils_avg(aws_client):
    target_instances = aws_client.get_target_instances()
    instance_ids = []
    cpu_sum = 0.0
    cpu_avg = 0.0
    point_counter = 0
    for instance in target_instances:
        start_time = datetime.utcnow() - timedelta(seconds = 2 * 60)
        end_time = datetime.utcnow()
        period = 60
        cpu_data = aws_client.get_cpu_utilization(instance['id'], start_time, end_time, period)
        for point in cpu_data:
            point_counter += 1
            cpu_sum += point[1]

    if int(point_counter) >= 1:
        cpu_avg = cpu_sum / float(point_counter)
        return cpu_avg

    return -1


def auto_scaling(aws_client):
    top_folder = Config.TOP_FOLDER
    policy_file_path = top_folder + '/app/auto-scaler/auto_scale.txt'
    pool_size_lower_bound = 1
    pool_size_upper_bound = 10

    cpu_grow_threshold = 0.0
    cpu_shrink_threshold = 0.0
    grow_ratio = 0.0
    shrink_ratio = 0.0
    auto_scale = 0

    if os.path.exists(policy_file_path):        
        with open(policy_file_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                cpu_grow_threshold = float(row[0])
                cpu_shrink_threshold = float(row[1])
                grow_ratio = float(row[2])
                shrink_ratio = float(row[3])
                auto_scale = int(row[4])
    else:
        logging.error('No policy file found')
        return None

    if int(auto_scale) == 1:
        target_instances = aws_client.get_target_instances()
        pool_size = len(target_instances)
        cpu_avg = cpu_utils_avg(aws_client = aws_client)
        # no valid instances
        logging.info('Avg CPU util is {}'.format(cpu_avg))
        logging.info('Current worker pool size is {}'.format(pool_size))
        if cpu_avg == -1:
            logging.error('No valid workers in the pool')
            return None
        # grow
        elif cpu_avg > cpu_grow_threshold:
            num_to_grow = int(pool_size * (grow_ratio - 1))
            if int(pool_size) >= pool_size_upper_bound:
                logging.warning('Pool size already exceeds the limit')
                return None
            elif int(pool_size + num_to_grow) >= pool_size_upper_bound:
                logging.warning('Grow to the limit')
                response = aws_client.grow_worker_by_some(int(pool_size_upper_bound - pool_size))
                logging.warning('Status are {}'.format(response))
                return 'Success'
            else:
                logging.warning('Grow {} instances'.format(num_to_grow))
                response = aws_client.grow_worker_by_some(num_to_grow)
                logging.warning('Status are {}'.format(response))
                return 'Success'
        # shrink
        elif cpu_avg < cpu_shrink_threshold:
            num_to_shrink = int(pool_size) - int(pool_size / shrink_ratio)
            if int(pool_size) <= pool_size_lower_bound:
                logging.warning('Pool size cannot be smaller')
                return None
            elif int(pool_size - num_to_shrink) <= pool_size_lower_bound:
                logging.warning('Shrink to the limit')
                response = aws_client.shrink_worker_by_some(int(pool_size - pool_size_lower_bound))
                logging.warning('Status are {}'.format(response))
                return 'Success'
            else:
                logging.warning('Shrink {} instances'.format(num_to_shrink))
                response = aws_client.shrink_worker_by_some(num_to_shrink)
                logging.warning('Status are {}'.format(response))
                return 'Success'
        else:
            logging.warning('Nothing changes')
            return None
    else:
        logging.error('Auto Scaling is not enabled')
        return None
            

if __name__ == '__main__':
    # initiate an aws client
    aws_client = AwsClient(
        access_key_id = Config.ACCESS_KEY_ID, 
        secrete_key = Config.SECRET_KEY, 
        region = Config.REGION, 
        template_id = Config.TEMPLATE_ID, 
        target_arn = Config.TARGET_ARN,
        elb_dns = Config.ELB_DNS)
    # start auto-scaling
    logging.getLogger().setLevel(logging.INFO)
    while True:
        response = auto_scaling(aws_client)
        if response == 'Success':
            # wait for 3 minutes, otherwise unstable
            logging.info('Grow or shrink successfully, wait for 5 min')
            time.sleep(300)
        else:
            time.sleep(60)
