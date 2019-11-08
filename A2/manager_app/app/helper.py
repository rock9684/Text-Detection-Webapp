from imutils.object_detection import non_max_suppression
from app import webapp, aws_client

# generate presigned url to get S3 stuff
def generate_presigned_url(name):
    url = aws_client.s3.generate_presigned_url('get_object',
        Params = {
            'Bucket': webapp.config["S3_BUCKET_NAME"],
            'Key': name,
        },
        ExpiresIn=3600)
    return url