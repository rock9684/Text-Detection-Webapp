from flask import Flask
from flask_login import LoginManager
from config import Config
import mysql.connector
import boto3

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

# s3 client
s3_client = boto3.client(
	's3', 
	aws_access_key_id = webapp.config['ACCESS_KEY_ID'],
	aws_secret_access_key = webapp.config['SECRET_KEY'],
	region_name = webapp.config['REGION'])

# cloud watch client
cw_client = boto3.client(
	'cloudwatch', 
	aws_access_key_id = webapp.config['ACCESS_KEY_ID'],
	aws_secret_access_key = webapp.config['SECRET_KEY'],
	region_name = webapp.config['REGION'])

# initialize loginManager
login_manager = LoginManager()
login_manager.init_app(webapp)
# when access login-required pages (by URL) without being logged in, will be redirected to the login page
login_manager.login_view = 'login'

from app import routes, models