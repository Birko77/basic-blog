"""Datastore models for user-accounts 

Classes:
User -- Model for the User-Objects
ResetPasswordRequest -- Model for reset-pasword requests 
DeactAccounts --  Model for storing deleted user-accounts
"""

import logging

from google.appengine.ext import db
from google.appengine.api import memcache

from utils import *


class User(db.Model):
    """Datastore model for the User-Objects

    Methods:
    by_id -- Return a User-object for a given User-id.
    update_user_cache -- Store a User-object in memcache.
    by_email -- Return a User-object for a given email.
    by_name -- Return a User-object for a given user-name.
    register -- Return a new User-object to store in the datastore.
    login_by_email -- Return a User-object after successful authentication.
    remove -- Delete a User-object from the datastore.
    """

    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)


    @classmethod
    def by_id(cls, uid):
        """Return a User-object for a given User-id.

        Read first from memcache. If User-object is not stored in memcache, 
        execute a Datastore query and update memcache.
        Return None if entity is not found.
        Argument:
        uid -- the User-id, this is the Datastore entity's key
        Return value:
        user -- the User-object for the given User-id, None if not found
        """

        user = memcache.get(str(uid))
        if user is None:
            user = User.get_by_id(int(uid))
            memcache.set(str(uid), user)
        return user

    @classmethod
    def update_user_cache(cls, user):
        """Store a User-object in memcache.

        Store a User-object in memcache. The key is the User-id .
        Argument:
        user -- the User-object to be stored in memcache
        """

        key = str(user.key().id())
        memcache.set(key, user)

    @classmethod
    def by_email(cls, email):
        """Return a User-object for a given email.

        Execute a Datastore query and filter by the given email.
        Return the first entity found. (emails should be unique)
        Argument:
        email -- the email associated with a user-account
        Return value:
        u -- the User-object for the given email, None if not found
        """

        u = User.all().filter('email', email).get()
        return u

    @classmethod
    def by_name(cls, name):
        """Return a User-object for a given user-name.

        Execute a Datastore query and filter by the given user-name.
        Return the first entity found. (user-names should be unique)
        Argument:
        name -- the user-name associated with a user-account
        Return value:
        u -- the User-object for the given user-name, None if not found
        """

        u = User.all().filter('name', name). get()
        return u

    @classmethod
    def register(cls, name, pw, email):
        """Return a new User-object to store in the datastore.

        Construct and return a new user-object with the given arguments.
        User-name and email are stored in clear text.
        The password is stored hashed and salted using the funktion 
        make_pw_hash(email, pw) which is imported from the utils module.
        Email and password are the required inputs to authenticate a user.
        Arguments:
        name -- a unique user-name [string]
        pw -- a password [string]
        email -- a unique email [string]
        Return value:
        the new User-object
        """

        pw_hash = make_pw_hash(email, pw)
        return User(name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login_by_email(cls, email, pw):
        """Return a User-object after successful authentication.

        Arguments:
        email -- a unique email [string]
        pw -- a password [string]
        Return value:
        u -- the User-object
        """

        u = cls.by_email(email)
        if u and valid_pw(email, pw, u.pw_hash):
            return u
    
    @classmethod
    def remove(cls, user_id):
        """Delete a User-object from the datastore.

        Delete user-object from datastore and memcache.

        Argument:
        user_id -- User-id
        """
        user = User.by_id(int(user_id))
        db.delete(user)

        key = str(user_id)
        memcache.delete(key)



class ResetPasswordRequest(db.Model):
    """Datastore model for the ResetPasswordRequest-Objects

    Methods:
    create_request -- Return a new ResetPasswordRequest-object.
    by_email -- Return most recent ResetPasswordRequest-object for given email.
    by_id -- Return the ResetPasswordRequest-object for a given request-id.
    check_for_valid_request -- Return ResetPasswordRequest-object 
    after successful authentication.
    """

    email = db.StringProperty(required = True)
    temp_pw_hash = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)


    @classmethod
    def create_request(cls, email, temp_pw):
        """Return a new ResetPasswordRequest-object.

        Construct and return a new ResetPasswordRequest-object with the given 
        arguments.
        Email is stored in clear text.
        The temp password is stored hashed and salted using the funktion 
        make_pw_hash(email, pw) which is imported from the utils module.
        Email and password are the required inputs to authenticate a user.

        Arguments:
        email -- user email [string]
        temp_pw -- randomly gnerated temporary password [string]
        Return value:
        the new ResetPasswordRequest-object
        """

        temp_pw_hash = make_pw_hash(email, temp_pw)
        return ResetPasswordRequest(email = email,
                    temp_pw_hash = temp_pw_hash)

    @classmethod
    def by_email(cls, email):
        """Return most recent ResetPasswordRequest-object for a given email.

        Argument:
        email -- user email
        Return value:
        r -- the most recent ResetPasswordRequest-object
        """

        r = ResetPasswordRequest.all().filter('email', email)\
            .order('-created').get()
        return r

    @classmethod
    def by_id(cls, rid):
        """Return the ResetPasswordRequest-object for a given request-id.

        Argument:
        rid -- request-id
        Return value:
        the ResetPasswordRequest-object
        """

        return ResetPasswordRequest.get_by_id(int(rid))

    @classmethod
    def check_for_valid_request(cls, email, temp_pw):
        """Return ResetPasswordRequest-object after successful authentication.

        Arguments:
        email -- the user email [string]
        temp_pw -- the temporary password [string]
        Return value:
        r -- the ResetPasswordRequest-object
        """

        r = cls.by_email(email)
        if r and valid_pw(email, temp_pw, r.temp_pw_hash):
            return r


class DeactAccounts(db.Model):
    """Datastore model for the DeactAccounts-Objects.

    The stored entities represent deleted user accounts.

    Methods:
    create -- Return a new DeactAccounts-object.
    """

    uid = db.IntegerProperty(required = True)
    name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)


    @classmethod
    def create(cls, uid, name, email):
        """Return a new DeactAccounts-object.

        Construct and return a new DeactAccounts-object with the given 
        arguments.

        Arguments:
        uid -- user-id [integer]
        name -- username [string]
        email -- user email [string]
        Return value:
        the new DeactAccounts-object
        """

        return DeactAccounts(uid = uid, name = name, email = email)

