from app import webapp, db, aws_client
from app.helper import generate_presigned_url
from flask import render_template, request, session, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime, timedelta
import os

@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('base.html')

@webapp.route('/list_workers', methods=['GET'])
def list_workers():
    target_instances = aws_client.get_target_instances()
    return render_template('worker_list.html', instances = target_instances)

@webapp.route('/elb_dns', methods=['GET'])
def elb_dns():
    elb_dns_url = 'http://' + aws_client.elb_dns
    return redirect(elb_dns_url) 

@webapp.route('/worker_view/<instance_id>', methods=['GET'])
def worker_view(instance_id):
	# set time range to be past 30 min
	# set period to 1 min
    start_time = datetime.utcnow() - timedelta(seconds = 30 * 60)
    end_time = datetime.utcnow()
    period = 60

    cpu_stats = aws_client.get_cpu_utilization(
    	instance_id = instance_id, 
    	start_time = start_time,
    	end_time = end_time,
    	period = period
    )

    http_stats = aws_client.get_http_request_rate(
    	instance_id = instance_id, 
    	start_time = start_time,
    	end_time = end_time,
    	period = period,
    	unit = 'Count'
    )

    return jsonify(cpu_stats, http_stats)

@webapp.route('/worker_view/grow_by_one', methods=['POST'])
def grow_by_one():
	try:
		response = aws_client.grow_worker_by_one()
		if int(response) != 200:
			return redirect(url_for('error'))
		else:
			return redirect(url_for('list_workers'))
	except Exception as e:
		return redirect(url_for('error'))

@webapp.route('/error', methods=['GET'])
def error():
	render_template('error.html')



















