# Text Detection Webapp
This is a text detection webapp based on University of Toronto's ECE1779 class

## Introduction
This is a webapp supposed to run on AWS. You can sign up or log in by a username and password. Then, you could upload photos and manage them. The webapp would detect texts in images. More details are provided in our reports.

## A1
A simple version of the webapp. It could be deployed on an EC2 instance and BOOM, it's ready for you to use. All user data and images stored locally on the instance.

## A2
A slightly complicated version of the webapp. It introduces two more components: a load balancer and a autoscaler. Except the user app described above, a new manager app is implemented. In the manager app, you could see cpu utilizations and HTTP request rates of existing servers and choose to add or remove servers so that the webapp could adapt to different traffic flows. And if you run the autoscaler, it would grow or shrink the number of servers according to preset thresholds. Also, data are stored in RDS instead of local DB and images are stored in S3.
