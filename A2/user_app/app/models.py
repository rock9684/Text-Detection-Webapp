from app import db, login_manager
from flask_login import UserMixin

class User(UserMixin):
    # inherit from flask-login class UserMixin so no need to define certain functions (e.g. is_authenticated(), is_active(), ...)
    def __init__(self, userid, username, salt, hhash):
        # match with the users table in the database, where relevant user account info is stored
        self.userid = userid    # unique (auto incremented as new user is added to database), 
                                # can be used to differentiate user and add to image names to make them unique too
        self.username = username    # unique, can be used to differentiate user
        # used to encrypt passwords, which should not be stored in plain text for security reasons
        self.salt = salt
        self.hhash = hhash 

    def get_id(self):
        '''
        return a value that can be used to determine a unique user; in this case, it is the unique username
        '''
        return self.username

    @staticmethod
    def get(username):
        '''
        static function, used to identify a unique user with a unique username and return a class object of the user
        '''
        cur = db.cursor() 
        # look for the user with this unique username in the database
        # error handling is performed by the function calling this function
        cur.execute("SELECT userid, salt, hhash FROM users WHERE username = '%s';" % (username))
        entry = cur.fetchone()
        cur.close()
        if (entry != None):
            # use the information found to make a class instance representing this user and return it
            return User(entry[0], username, entry[1], entry[2])
        return None


@login_manager.user_loader
def load_user(username):
    '''
    This callback is used by loginManager to reload the user object from the user ID stored in the session
    It takes in the unique username of a user, and return the corresponding user object
    '''
    return User.get(username)