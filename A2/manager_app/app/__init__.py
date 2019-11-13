from flask import Flask
from config import Config
import mysql.connector
import boto3
import csv
from app import aws

# create flask instance
webapp = Flask(__name__)
# configure the instance using variables defined in config.py
webapp.config.from_object(Config)

# configure and connect to database
db = mysql.connector.connect(
    user=webapp.config['USERNAME'],
    password=webapp.config['PASSWORD'],
    host=webapp.config['HOSTNAME'],
    database=webapp.config['DATABASE'])

# aws client
aws_client = aws.AwsClient(
	access_key_id = webapp.config['ACCESS_KEY_ID'], 
	secrete_key = webapp.config['SECRET_KEY'], 
	region = webapp.config['REGION'], 
	template_id = webapp.config['TEMPLATE_ID'], 
	target_arn = webapp.config['TARGET_ARN'],
	elb_dns = webapp.config['ELB_DNS'])

# initialize worker pool
target_instances = aws_client.get_target_instances()
instance_ids = []
for instance in target_instances:
	instance_ids.append(instance['id'])

worker_pool_size = len(instance_ids)
if worker_pool_size != 1:
	# alter worker pool
	if worker_pool_size < 1:
		# create one
		aws_client.grow_worker_by_one()
	else:
		# cut some
		num_to_cut = worker_pool_size - 1
		aws_client.shrink_worker_by_some(num_to_cut)

# initialize autl-scaler policy and disable auto-scaler
top_folder = webapp.config['TOP_FOLDER']

with open(top_folder + '/app/auto-scaler/auto_scale.txt', 'w', newline='') as csvfile:
	writer = csv.writer(csvfile, delimiter = ',')
	writer.writerow([0,0,0,0,0])

from app import routes