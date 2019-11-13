from flask import Flask
from config import Config
import mysql.connector
import boto3
from app import aws

# create flask instance
webapp = Flask(__name__)
# configure the instance using variables defined in config.py
webapp.config.from_object(Config)

# configure and connect to database
db = 0

# aws client
aws_client = aws.AwsClient(
	access_key_id = webapp.config['ACCESS_KEY_ID'], 
	secrete_key = webapp.config['SECRET_KEY'], 
	region = webapp.config['REGION'], 
	template_id = webapp.config['TEMPLATE_ID'], 
	target_arn = webapp.config['TARGET_ARN'],
	elb_dns = webapp.config['ELB_DNS'])

from app import routes