. /home/ubuntu/venv/bin/activate
alias proj="cd /home/ubuntu/Desktop/ece1779_lab/A2/manager_app/app/auto-scaler/"
python3 auto_scaler.py &
/home/ubuntu/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers=1 --chdir /home/ubuntu/Desktop/ece1779_lab/A2/manager_app app:webapp