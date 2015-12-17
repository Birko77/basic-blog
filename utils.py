import re
import os
import random
import string
import hashlib
import hmac
from string import ascii_letters


# --- HASH COOKIES ---

SECRET = 'MY_SUPER_SECRET'

def hash_str(val):
    return hmac.new(SECRET, val).hexdigest()

def make_secure_val(val):
    return "%s|%s" % (val, hash_str(val))

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if make_secure_val(val) == secure_val:
        return val


# --- VERIFY USER INPUT ---

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASS_RE = re.compile(r"^(?=.*?\d)(?=.*?[A-Z])(?=.*?[a-z])[A-Za-z0-9_-]{8,20}$")
def valid_password(password):
    return PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return EMAIL_RE.match(email)

def valid_verify(value, verify):
    if value==verify:
        return True

TITLE_RE = re.compile(r"^.{1,78}$")
def valid_title(title):
    return TITLE_RE.match(title)

BODY_RE = re.compile(r"^(.|\n){1,20000}$")
def valid_body(body):
    return BODY_RE.match(body)

SUBJECT_RE = re.compile(r"^.{1,78}$")
def valid_subject(subject):
    return SUBJECT_RE.match(subject)

CONTENT_RE = re.compile(r"^(.|\n){1,1000}$")
def valid_content(content):
    return CONTENT_RE.match(content)


# --- HASH AND SALT PASSWORDS ---

# Generate secure password_hash for storing in DB and 
# verify login_name and pw from login.
# Login_name can be username, email or similar. 
# Used by the decorator methods register and login.
def make_salt(length = 10):
    return ''.join(random.choice(ascii_letters)for x in xrange(length))

def make_pw_hash(login_name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(login_name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(login_name, password, pw_hash):
    salt = pw_hash.split(',')[0]
    return pw_hash == make_pw_hash(login_name, password, salt)
    #pw_hash is safed in the database. pw_hash = "salt,hash_value".  

