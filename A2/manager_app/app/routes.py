from app import webapp, db, aws_client
from app.helper import generate_presigned_url
from flask import render_template, request, session, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import timedelta
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