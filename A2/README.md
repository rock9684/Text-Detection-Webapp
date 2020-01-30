# A2
Basic the same as A1's application.
Instead, use aws RDS but not local database and use S3 to store images but not local storage.
Also has three more components, a load balancer, a autoscaler and a manager app.

## Load Balancer
A load balancer is basically used to distribute internet traffic to different servers. In our webapp, we uses AWS's load balancer directly.

## Autoscaler
A autoscaler is used to grow or shrink the amount of servers automatically. Our autoscaler could adjust the number of servers between 1 and 10 according to predefined thresholds. Simply run the script and it will do the work.

## Manager App
Here, you could 
See all servers in use and their cpu utilizations and http request rates. 
Choose to remove or add a server. 
Remove all servers. 
Shutdown the webapp and delte all data in RDS and S3.
Enable the autoscaler and set thresholds.
