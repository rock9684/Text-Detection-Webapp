from app import webapp, db, s3_client
from app.models import User
from app.helper import detect_text
from flask import render_template, request, session, redirect, url_for, jsonify, flash
import hashlib, uuid
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import timedelta
import os

@webapp.before_request
def make_session_permanent():
    '''
    Set permanent session for 24h
    '''
    session.permanent = True
    webapp.permanent_session_lifetime = timedelta(hours=24)

@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/home', methods=['GET', 'POST'])
def home():
    '''
    Specify what happens when the home link is accessed
    '''
    # Message displayed will be slightly different depending on if the user is logged in or not
    if (current_user.is_authenticated):
        return render_template('home.html')
    return render_template('home.html', loggedin=1)

############
## signup ##
############

@webapp.route('/signup', methods=['GET', 'POST'])
def signup():
    '''
    Specify what happens when the signup link is accessed.
    If signup is successful, the user will be added into database, logged in and redirected to the myphotos page.
    If signup failed, an error page with proper messages will be redirected to.

    The users table in the database have the following columns:
        userid, username, salt, hhash, count (i.e. # of images the user uploaded)

    userid is unique, as it will be automatically incremented as new entry (i.e. new user) is added to the table.
    username is also set to be unique, so addition of duplicate username will cause an exception to be raised.
    salt value will be per-user.
    hhash will be the encrypted version of the password user input.
    '''
    # If user is logged in, access to the login page will direct user to myphotos 
    if (current_user.is_authenticated):
        return redirect(url_for('myphotos'))
    if request.method == 'POST':
        # read user input to the form
        username = request.form.get('username')
        password = request.form.get('password')
        # Do not allow empty username and/or password
        if username == '' or password == '':
            return render_template('error.html', error="Empty field(s) is not allowed.")
        # encrpt the plain text password 
        salt = uuid.uuid4().hex
        hhash = hashlib.sha256(password.encode() + salt.encode()).hexdigest()
        # access the database
        cur = db.cursor()
        # insert user-input username and password into the users table
        try:
            cur.execute("INSERT INTO users (username, salt, hhash, count) VALUES ('%s', '%s', '%s', '%d');" % (username, salt, hhash, 0))
        except Exception as e:
            db.rollback()
            cur.close()
            # exception caused by duplicate username
            if (e.args[0] == 1062):
                e = "Username has already been registered!"
            # exception caused by username being too long (limit is 50 characters)
            elif (e.args[0] == 1406):
                e = "Username is too long!"
            # handle any other database errors
            return render_template('error.html', error=e)
        db.commit()
        # Now that signup complete successfully, log in the newly registered user with flask-login
        user = User.get(username)
        cur.close()
        login_user(user)
        # flash a message on website to let users know they have succesfully signed up and logged in.
        flash("Your account is created successfully and you are now logged in! Start by uploading your first photo.")
        return redirect(url_for('myphotos'))
    return render_template('signup.html')

###########
## login ##
###########

@webapp.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Specify what happens when the login link is accessed.
    If login is successful, the user will be logged in and redirected to the myphotos page.
    If login failed, an error page with proper messages will be redirected to.
    '''
    # If user is logged in, access to the login page will direct user to myphotos 
    if (current_user.is_authenticated):
        return redirect(url_for('myphotos'))
    if request.method == 'POST':
        # read user input to the form
        username = request.form.get('username')
        password = request.form.get('password')
        # Do not allow empty username and/or password
        if username == '' or password == '':
            return render_template('error.html', error="Empty field(s) is not allowed.")
        # look for the user in the database
        user = User.get(username)
        # handle the case where no such username exists
        if (user == None):
            return render_template('error.html', error="Username does not exist!")
        # handle the case where password for a username does not match record
        veryfied_password = hashlib.sha256(password.encode() + user.salt.encode()).hexdigest()
        if (veryfied_password == user.hhash):
            login_user(user)
            # flash a message on website to let users know that they are now logged in. 
            flash("You successfully logged in!")
            return redirect(url_for('myphotos'))
        else:
            return render_template('error.html', error="Incorrect password!")
    return render_template('login.html')

############
## logout ##
############

@webapp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    '''
    Specify what happens when the logout link is accessed.
    Only logged in users can access this link; others will be redirected to the login page.
    '''
    logout_user()
    # flash a message on website to let users know that they are now logged out. 
    flash("You successfully logged out!")
    return redirect(url_for('home'))

##############
## myphotos ##
##############

@webapp.route('/myphotos')
@login_required
def myphotos():
    '''
    Specify what happens when the myphotos link is accessed.
    Only logged in users can access this link; others will be redirected to the login page.
    '''
    # access database
    cur= db.cursor()
    # get info of all images uploaded by the current logged-in user
    try:
        cur.execute('SELECT namebase, extension FROM images WHERE userid = %s' % (current_user.userid))
    except Exception:
        cur.close()
        return render_template('error.html')
    result = cur.fetchall()
    cur.close()
    # display thumbnails of all images uploaded by the current logged-in user, the details of which is handled in html
    return render_template('myphotos.html', username=current_user.username, result=result)

############
## upload ##
############

@webapp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    '''
    Specify what happens when the login link is accessed.
    Only logged in users can access this link; others will be redirected to the login page.

    The images table in the database have the following columns:
        imid, userid, namebase, extension

    For an uploaded file, only its filename, seprated into namebase and extension, will be saved into the database.
    The image file itself is stored into the local file system, together with its thumbnail and opencv processed version with text detection. 

    Duplicate filenames are okay since each will have the userid and count added to the path they are saved locally. 
    The actual path an image is saved will be: 
        webapp.config["SAVE_FOLDER"]/namebase_userid_count.extension
    Its thumbnail path will be:
        webapp.config["SAVE_FOLDER"]/namebase_userid_count_tn.extension
    Its opencv-processed version path will be:
        webapp.config["SAVE_FOLDER"]/namebase_userid_count_cv.extension
    '''
    if request.method == 'POST':
        # get info about the user-uploaded image
        try:
            file = request.files['image']
        # Do not allow images bigger than 10M
        except RequestEntityTooLarge:
            return render_template('error.html', error="Image exceeds size limit (10M).")
        # Do not allow empty upload
        if file.filename == '':
            return render_template('error.html', error="No image selected.")
        # Get a secure version of the filenmae
        filename = secure_filename(file.filename)
        print(filename)
        # Separate filename and extension for easier name composition for original, thumbnail and opencv processed version
        filename, extension = filename.rsplit('.', 1)
        # Only allow JPG and PNG images
        if extension not in ['jpg', 'jpeg', 'png']:
            return render_template('error.html', e="Only JPG and PNG images are allowed!")

        # access database
        cur = db.cursor()
        # read count from table users for naming the uploaded image
        try:
            cur.execute("SELECT count FROM users WHERE userid = '%d';" % (current_user.userid))
        except Exception:
            cur.close()
            return render_template('error.html')
        count = cur.fetchone()
        if (count == None):
            return render_template('error.html')
        count = count[0]
        
        # compose the namebase
        namebase = '_'.join([filename, str(current_user.userid), str(count)])
        # insert new entry (i.e. new image) into the users table
        try:
            cur.execute("INSERT INTO images (userid, namebase, extension) VALUES ('%s', '%s', '%s');" % (current_user.userid, namebase, extension))
        except Exception:
            db.rollback()
            cur.close()
            return render_template('error.html')
        db.commit()

        # if successfully uploadded, update count in users table
        try:
            cur.execute("UPDATE users SET count = '%d' WHERE userid = '%d';" % (count + 1, current_user.userid))
        except Exception:
            db.rollback()
            cur.close()
            return render_template('error.html')

        # compose all names
        imname_base = namebase + '.' + extension
        tnname_base = namebase + '_tn.gif'
        cvname_base = namebase + '_cv.' + extension
        imname = webapp.config["SAVE_FOLDER"] + '/' + imname_base
        tnname = webapp.config["SAVE_FOLDER"] + '/' + tnname_base
        cvname = webapp.config["SAVE_FOLDER"] + '/' + cvname_base
        # save the original image
        file.save(imname)

        # save the thumbnail
        cmd_convert = "convert %s -auto-orient -thumbnail '200x200>' -gravity center -extent 200x200 -unsharp 0x.5 %s" % (imname, tnname)
        result_convert = os.system(cmd_convert)
        if (result_convert != 0): # if successfully converted, result_convert should have vlaue 0
            db.rollback()
            cur.close()
            return render_template('error.html', e="Thumbnail creation failed, please re-upload.")

        # save the image with text detected using opencv
        success = detect_text(webapp.config["TOP_FOLDER"], imname, cvname)
        if not success:
            db.rollback()
            cur.close()
            return render_template('error.html', e="Text detection failed, please re-upload.")

        # upload to s3
        try:
            s3_client.upload_file(imname, webapp.config["S3_BUCKET_NAME"], imname_base)
            s3_client.upload_file(tnname, webapp.config["S3_BUCKET_NAME"], tnname_base)
            s3_client.upload_file(cvname, webapp.config["S3_BUCKET_NAME"], cvname_base)
        except Exception:
            db.rollback()
            cur.close()
            return render_template('error.html', e="Cannot upload image")

        db.commit()
        cur.close()

        # remove temp files
        os.remove(imname)
        os.remove(cvname)
        os.remove(tnname)

        # flash the message to let users know that image uploading is successful
        flash("The new photo is successfully uploaded!")
        # display the original image and the version with text deteced side by side
        return render_template('display.html', imname=namebase + '.' + extension, cvname=namebase + '_cv.' + extension)
    return render_template('upload.html')

#############
## display ##
#############

@webapp.route('/display/<string:imname>/<string:cvname>', methods=['GET', 'POST'])
@login_required
def display(imname=None, cvname=None):
    '''
    Specify what happens when the display link is accessed.
    Only logged in users can access this link; others will be redirected to the login page.

    This webpage displays an original photo and its opencv processed version side by side.
    This webpage can be accessedd in 3 ways: 1) after successful upload; 2) after clicking on thumbnails on myphotos page; 3) url.

    For 2), the redirect is handled in html, which makes it necessary to have the two extra variables in the url

    For 3), user might try to access others photos by guessing the image names to compose the url. 
    We specifically check the owner of the images about to be displayed to prevent this illegal access from happening.
    '''
    # recover namebase and extension from imname
    namebase, extension = imname.rsplit('.', 1)
    # make sure the imname and cvname correspond to each other
    if (namebase+'_cv' != cvname.rsplit('.', 1)[0]):
        return render_template('error.html', error='Wrong access! Please display photos by choosing from "My Photos" page.')
    # access database
    cur = db.cursor()
    # retrieve info about the user who uploaded this photo
    try:
        cur.execute("SELECT userid FROM images WHERE namebase = '%s' AND extension = '%s';" % (namebase, extension))
    except Exception:
        db.rollback()
        cur.close()
        return render_template('error.html')
    userid = cur.fetchone()[0]
    cur.close()
    # check if the photo's owner matches current user
    if (userid == None) or (userid != current_user.userid):
        return render_template('error.html', error='Wrong access! Please display photos by choosing from "My Photos" page.')
    return render_template('display.html', imname=imname, cvname=cvname)

#########################################################
#################### API for Testing ####################
#########################################################

##################
## register api ##
##################

@webapp.route('/api/register', methods=['POST'])
def api_register():
    '''
    API especially for test
    '''
    username = request.form.get('username')
    password = request.form.get('password')

    if username == '' or password == '':
        # Forbidden
        return jsonify("Empty field(s) is not allowed."), 403

    salt = uuid.uuid4().hex
    hhash = hashlib.sha256(password.encode() + salt.encode()).hexdigest()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO users (username, salt, hhash, count) VALUES ('%s', '%s', '%s', '%d');" % (username, salt, hhash, 0))
    except Exception as e:
        db.rollback()
        cur.close()
        if (e.args[0] == 1062):
            e = "Username has already been registered!"
            # Conflict
            return jsonify(e), 409
        elif (e.args[0] == 1406):
            # Forbidden
            e = "Username is too long!"
            return jsonify(e), 403
    db.commit()
    user = User.get(username)
    if (user == None):
        # Internal server error
        return jsonify("Database error; cannot add user"), 500
    cur.close()
    login_user(user)
    return jsonify("Successfully registered"), 200

################
## upload api ##
################

@webapp.route('/api/upload', methods=['POST'])
def api_upload():
    '''
    API especially for load_generator to test
    '''
    # check user info and login first
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.get(username)
    if (user == None):
        # unauthorized
        return jsonify("Username does not exist!"), 401
    veryfied_password = hashlib.sha256(password.encode() + user.salt.encode()).hexdigest()
    if (veryfied_password == user.hhash):
        login_user(user)
    else:
        # unauthorized
        return jsonify("Incorrect password!"), 401

    # get info about the user-uploaded image
    try:
        file = request.files['file']
    # Do not allow images bigger than 10M
    except RequestEntityTooLarge:
        # forbidden
        return jsonify("Image exceeds size limit (10M)."), 403
    # Do not allow empty upload
    if file.filename == '':
        # forbidden
        return jsonify("No image selected."), 403
    # Get a secure version of the filenmae
    filename = secure_filename(file.filename)
    # Separate filename and extension for easier name composition for original, thumbnail and opencv processed version
    filename, extension = filename.rsplit('.', 1)
    
    # access database
    cur = db.cursor()
    # read count from table users for naming the uploaded image
    try:
        cur.execute("SELECT count FROM users WHERE userid = '%d';" % (current_user.userid))
    except Exception:
        cur.close()
        # internal server error
        return jsonify("Database error: cannot read column `count`"), 500
    count = cur.fetchone()
    if (count == None):
        return jsonify("Database error: cannot read column `count`"), 500
    count = count[0]
    
    # compose the namebase
    namebase = '_'.join([filename, str(current_user.userid), str(count)])
    # insert new entry (i.e. new image) into the users table
    try:
        cur.execute("INSERT INTO images (userid, namebase, extension) VALUES ('%s', '%s', '%s');" % (current_user.userid, namebase, extension))
    except Exception:
        db.rollback()
        cur.close()
        # internal server error
        return jsonify("Database error: cannot insert into `images`"), 500
    db.commit()

    # if successfully uploadded, update count in users table
    try:
        cur.execute("UPDATE users SET count = '%d' WHERE userid = '%d';" % (count + 1, current_user.userid))
    except Exception:
        db.rollback()
        cur.close()
        return jsonify("Database error: cannot update column `count`"), 500

    # compose all names
    imname_base = namebase + '.' + extension
    tnname_base = namebase + '_tn.gif'
    cvname_base = namebase + '_cv.' + extension
    imname = webapp.config["SAVE_FOLDER"] + '/' + imname_base
    tnname = webapp.config["SAVE_FOLDER"] + '/' + tnname_base
    cvname = webapp.config["SAVE_FOLDER"] + '/' + cvname_base

    # save the original image
    file.save(imname)
    # save the thumbnail
    cmd_convert = "convert %s -auto-orient -thumbnail '200x200>' -gravity center -extent 200x200 -unsharp 0x.5 %s" % (imname, tnname)
    result_convert = os.system(cmd_convert)
    if (result_convert != 0): # if successfully converted, result_convert should have vlaue 0
        db.rollback()
        cur.close()
        return jsonify("Error: cannot create a thumnail"), 500
    # save the image with text detected using opencv
    success = detect_text(webapp.config["TOP_FOLDER"], imname, cvname)
    if not success:
        db.rollback()
        cur.close()
        return jsonify("Text detection failed, please re-upload."), 500

    # upload to s3
    try:
        s3_client.upload_file(imname, webapp.config["S3_BUCKET_NAME"], imname_base)
        s3_client.upload_file(tnname, webapp.config["S3_BUCKET_NAME"], tnname_base)
        s3_client.upload_file(cvname, webapp.config["S3_BUCKET_NAME"], cvname_base)
    except Exception:
        db.rollback()
        cur.close()
        return jsonify("Cannot upload image"), 500

    db.commit()
    cur.close()
    # remove temp files
    os.remove(imname)
    os.remove(cvname)
    os.remove(tnname)
    # flash the message to let users know that image uploading is successful
    flash("The new photo is successfully uploaded!")
    # display the original image and the version with text deteced side by side
    return jsonify("Successfully uploaded"), 200

    


