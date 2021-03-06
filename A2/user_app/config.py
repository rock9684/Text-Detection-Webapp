import os
# get the top level folder for this project
dir_path = os.path.dirname(os.path.realpath(__file__))

# get ec2 instance id
instance_id = os.popen('ec2metadata --instance-id').read().strip()

# define environment vaiables
class Config(object):
    # A random key generated by command:
    #   python -c 'import os; print(os.urandom(16))'
    # This is required for Flask sessions, which allows you to store information 
    # specific to a user from one request to the next.
    SECRET_KEY = b'\xcd^;\x00\x88T\xfc\xdc(7\x8a\x92\x02\x06\xd5\x16'
    # Limit the size of input files to be no bigger than 10M
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    # Variables to configure database
    USERNAME = ''
    PASSWORD = ''
    HOSTNAME = ''
    DATABASE = ''
    # Top level folder path
    TOP_FOLDER = dir_path
    # aws credentials
    ACCESS_KEY_ID = ''
    SECRET_KEY = ''
    REGION = 'us-east-1'
    # ec2 instance id
    INSTANCE_ID = instance_id
    # S3 configuration
    S3_BUCKET_NAME = 'ece1779-bucket'
    # To display an image on website using Flask, it needs to be placed in this folder
    # As a result, all user uploaded images and their corresponding thumbnails and 
    # OpenCV processed images with text detection will be stored here
    SAVE_FOLDER = dir_path + '/app/static'
