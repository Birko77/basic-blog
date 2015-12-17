import re
import os
import random
import hashlib
import hmac
import time
import datetime
from string import ascii_letters
import logging

from google.appengine.api import memcache

from utils import *
from handler import Handler
from user_database import User, ResetPasswordRequest, DeactAccounts
from article_database import Article, DeletdArticle

# --- USER SIGNUP - LOGNIN - LOGOUT ---

class SignupHandler(Handler):

    def get(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_signup_1 = True)
        else:
            state = self.make_state()
            self.render('signup.html', state = state)

    def post(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_signup_1 = True)
        else:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            input_username = self.request.get('username')
            input_password = self.request.get('password')
            input_verify_password = self.request.get('verify_password')
            input_email = self.request.get('email').lower()
            input_verify_email = self.request.get('verify_email').lower()

            error_username=""
            error_password=""
            error_verify_password=""
            error_email=""
            error_verify_email=""
            error_username_exists=""
            error_user_exists=""

            have_error = False

            if not valid_username(input_username):
                # Show the error-message: not a valid username.
                error_username = True
                have_error = True
            if not valid_password(input_password):
                # Show the error-message: not a valid password.
                error_password = True
                have_error = True
            if not valid_verify(input_password, input_verify_password):
                # Show the error-message: passwords do not match.
                error_verify_password = True
                have_error = True
            if not valid_email(input_email):
                # Show the error-message: not a valid email.
                error_email = True
                have_error = True
            if not valid_verify(input_email, input_verify_email):
                # Show the error-message: emails do not match.
                error_verify_email = True
                have_error = True
            if have_error == False:
                u = User.by_name(input_username)
                if u:
                    # Show the error-message: username is already taken.
                    error_username_exists = True
                    have_error = True
                    
                u = User.by_email(input_email)
                if u:
                    # Show the error-message: email already used.
                    error_user_exists = True
                    have_error = True

            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('signup.html',
                            error_username = error_username,
                            error_username_exists = error_username_exists,
                            error_password = error_password,
                            error_verify_password = error_verify_password,
                            error_email = error_email,
                            error_verify_email = error_verify_email,
                            error_user_exists = error_user_exists,
                            username_form = input_username,
                            email_form = input_email,
                            verify_email_form = input_verify_email,
                            state = state)
            else:
                #Create new entry in the User-DB.
                u = User.register(input_username, input_password, input_email)
                u.put()
                #update memcache
                User.update_user_cache(u)

                #Send confirmation email
                self.send_email(u.email, 
                                'email_subject.html', 
                                'email_welcome.html', 
                                subject_type = 'welcome', 
                                username = u.name, 
                                user_email = u.email)
                
                #Set cookie and render message page with welcome
                self.login(u)
                self.render('message.html', user = u, message_signup_2 = True)


class LoginHandler(Handler):

    def get(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_login_1 = True)
        else:
            state = self.make_state()
            self.render('login.html', state = state)

    def post(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_login_1 = True)
        else:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            input_email = self.request.get('email').lower()
            input_password = self.request.get('password')

            error=""

            u = User.login_by_email(input_email, input_password)
            if u:
                self.login(u)
                self.redirect('/')
            else:
                state = self.make_state()
                # Render page with error-messages.
                self.render('login.html', 
                            error = True, 
                            email_form = input_email,
                            state = state)


class LogoutHandler(Handler):

    def get(self):
        if self.user:
            self.logout()
            # Show message that user has been logged out.
            self.render('message.html', 
                        message_logout_1 = True,
                        logout_name = self.user.name)
        else:
            self.redirect("/")


# --- PASSWORD RESET ---

class ForgotPasswordHandler(Handler):

    def get(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_forgot_password_1 = True)
        else:
            state = self.make_state()
            self.render('forgot_password.html', state = state)

    def post(self):
        if self.user:
            # Prompt user to log out.
            self.render('message.html', 
                        user = self.user, 
                        message_forgot_password_1 = True)
        else:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return
            # Receive input from web-page: eamil
            input_email = self.request.get('email').lower()

            error = ''
            self.user = User.by_email(input_email)
            if not self.user:
                state = self.make_state()
                # Render page with error-message.
                self.render('forgot_password.html', 
                            form_email = input_email, 
                            error = True,
                            state = state)
            else:
                # Generate new temporary random password
                length = 10
                temp_pw = ''.join(random.choice(ascii_letters)for x in xrange(length))

                # Create entry in ResetPasswordRequest DB
                u = ResetPasswordRequest.create_request(input_email, temp_pw)
                u.put()

                # Send email with a link to the ResetPassword page. 
                # The link includes email and temporary password to 
                # authenticate the user.
                # ADAPT LINK TO GAE URL
                resetToken = str(u.key().id())+"-"+temp_pw
                link = "http://PROJECT_ID.appspot.com/reset_pw/?token=%s" %(resetToken)

                self.send_email(self.user.email, 
                                'email_subject.html', 
                                'email_forgot_password.html', 
                                subject_type = 'forgot_password', 
                                username = self.user.name, 
                                link = link)

                # Render message-page with message that email was sent
                self.render('message.html', 
                            input_email = input_email, 
                            message_forgot_password_2 = True)
                logging.error(link)


class ResetPasswordHandler(Handler):

    def get(self):
        if self.user:
            # Prompt user to logout
            self.render('message.html', 
                        user = self.user, 
                        message_reset_password_1 = True)
        else:
            # Get token from URL
            input_token = self.request.get('token')

            # Check if format of token is valid 
            TOKEN_RE = re.compile(r"^([0-9]{1,30})\-.{3,20}$")
            if not TOKEN_RE.match(input_token):
                # Set invalid reset_id so that a normal error message is sent
                reset_id = 1
            else:
                # Split token to obtain reset_id and temp_pw.
                reset_id = int(input_token.split('-')[0])
                temp_pw = input_token.split('-')[1]

            # Use reset_id to find entry in ResetPasswordRequest DB.
            self.p = ResetPasswordRequest.by_id(reset_id)
            # Check if entry exists 
            if not self.p:
                # Show message that link is not valid.
                self.render('message.html', message_reset_password_2 = True)

            # Check if entry is not older than one hour.
            elif datetime.datetime.now() - datetime.timedelta(hours = 1) > self.p.created:
                # Show message that too much time has passed.
                self.render('message.html', message_reset_password_3 = True)

            # Check if temp_pw is valid
            elif not ResetPasswordRequest.check_for_valid_request(self.p.email, temp_pw):
                # Show message that the link is not valid.
                self.render('message.html', message_reset_password_4 = True)

            # If no error, get user by_email, 
            # log in and render reset_password.html 
            else:
                email = self.p.email
                self.user = User.by_email(email)
                self.login(self.user)
                state = self.make_state()
                self.render('reset_password.html', 
                            user = self.user, 
                            token = input_token,
                            state = state) 
    
    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            # Get user input: password and verify_password
            input_password = self.request.get('password')
            input_verify_password = self.request.get('verify_password')
            # Get token from web page
            input_token = self.request.get('token')

            # Check if token is valid
            TOKEN_RE = re.compile(r"^([0-9]{1,30})\-.{3,20}$")
            if not TOKEN_RE.match(input_token):
                # Set invalid reset_id so that a normal error message is sent
                reset_id = 1
            else:
                reset_id = int(input_token.split('-')[0])
                temp_pw = input_token.split('-')[1]

            # Use reset_id to find entry in ResetPasswordRequest DB.
            self.p = ResetPasswordRequest.by_id(reset_id)
            # Check if entry exists 
            if not self.p:
                # Show message to contact via email
                self.render('message.html', 
                            user = self.user, 
                            message_reset_password_5 = True)

            #Check if entry is not older than one hour.
            elif datetime.datetime.now() - datetime.timedelta(hours = 1) > self.p.created:
                # Show message that too much time has passed.
                self.render('message.html', 
                            user = self.user, 
                            message_reset_password_3 = True)

            #Check if temp_pw is valid
            elif not ResetPasswordRequest.check_for_valid_request(self.p.email, temp_pw):
                # Show message to contact via email
                self.render('message.html', 
                            user = self.user, 
                            message_reset_password_5 = True)
            else:
                # Check if password and verify_password are valid. 
                # Set error-messages. 
                error_password=""
                error_verify_password=""

                have_error = False

                if not valid_password(input_password):
                    # Show the error-message: not a valid password.
                    error_password = True
                    have_error = True
                if not valid_verify(input_password, input_verify_password):
                    # Show the error-message: passwords do not match.
                    error_verify_password = True
                    have_error = True

                if have_error:
                    state = self.make_state()
                    # Render page with error-messages.
                    self.render('reset_password.html',
                                user = self.user,
                                token = input_token,
                                error_password = error_password,
                                error_verify_password = error_verify_password,
                                state = state)
                else:
                    # Generate password-hash and store in DB
                    pw_hash = make_pw_hash(self.user.email, input_password)
                    self.user.pw_hash = pw_hash
                    self.user.put()
                    # Update memcache
                    User.update_user_cache(self.user)

                    # Invalidate entity in ResetPasswordRequest db
                    self.p = ResetPasswordRequest.by_email(self.user.email)
                    self.p.temp_pw_hash = "deactivated"
                    self.p.put()

                    # Show message that the password has been changed.
                    self.render('message.html', 
                                user = self.user, 
                                message_reset_password_7 = True)


        else:
            # Show message to use the linke in the email.
            self.render('message.html', 
                        user = self.user, 
                        message_reset_password_6 = True)


# --- USER SETTINGS ---

class UserSettingsHandler(Handler):

    def get(self):
        if self.user:
            self.render('user_settings.html', user = self.user)
        else:
            # Prompt user to login.
            self.render('message.html', message_user_settings_1 = True)


class ChangePasswordHandler(Handler):

    def get(self):
        if self.user:
            state = self.make_state()
            self.render('change_password.html', 
                        user = self.user,
                        state = state)
        else:
            # Prompt user to login.
            self.render('message.html', 
                        message_user_settings_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            # Get user input
            input_current_password = self.request.get('current_password')
            input_password = self.request.get('password')
            input_verify_password = self.request.get('verify_password')

            # Check input and set error messages. 
            error_current_password=""
            error_password=""
            error_verify_password=""

            have_error = False

            if not valid_pw(self.user.email, input_current_password, self.user.pw_hash):
                # Set the error-message: incorrect password.
                error_current_password = True
                have_error = True
            if not valid_password(input_password):
                # Set the error-message: not a valid password.
                error_password = True
                have_error = True
            if not valid_verify(input_password, input_verify_password):
                # Set the error-message: passwords do not match.
                error_verify_password = True
                have_error = True
 
            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('change_password.html',
                            user = self.user,
                            error_current_password = error_current_password,
                            error_password = error_password,
                            error_verify_password = error_verify_password,
                            state = state)
            else:
                # Generate password-hash and store in DB
                pw_hash = make_pw_hash(self.user.email, input_password)
                self.user.pw_hash = pw_hash
                self.user.put()
                # Update memcache
                User.update_user_cache(self.user)

                state = self.make_state()
                # Render page with success message.
                self.render('change_password.html', 
                            user = self.user, 
                            success_message = True,
                            state = state)
        else:
            # Prompt user to login.
            self.render('message.html', 
                        message_user_settings_1 = True)


class ChangeEmailHandler(Handler):

    def get(self):
        if self.user:
            state = self.make_state()
            self.render('change_email.html', 
                        user = self.user,
                        state = state)
        else:
            # Prompt user to login.
            self.render('message.html', 
                        message_user_settings_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            # Get user input
            input_current_password = self.request.get('current_password')
            input_email = self.request.get('email').lower()
            input_verify_email = self.request.get('verify_email').lower()

            # Check input and set error messages. 
            error_current_password=""
            error_email=""
            error_verify_email=""
            error_user_exists=""

            have_error = False

            if not valid_pw(self.user.email, input_current_password, self.user.pw_hash):
                # Set the error-message: incorrect password.
                error_current_password = True
                have_error = True
            if not valid_email(input_email):
                # Set the error-message: not a valid email.
                error_email = True
                have_error = True
            if not valid_verify(input_email, input_verify_email):
                # Set the error-message: emails do not match.
                error_verify_email = True
                have_error = True

            if have_error == False:
                u = User.by_email(input_email)
                if u:
                    # Set the error-message: email already assigned.
                    error_user_exists = True
                    have_error = True
 
            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('change_email.html',
                            user = self.user,
                            email = input_email,
                            error_current_password = error_current_password,
                            error_email = error_email,
                            error_verify_email = error_verify_email,
                            error_user_exists = error_user_exists,
                            state = state)
            else:
                # Generate password-hash
                # Store new email and password-hash in DB
                pw_hash = make_pw_hash(input_email, input_current_password)
                self.user.pw_hash = pw_hash
                self.user.email = input_email
                self.user.put()
                # Update memcache
                User.update_user_cache(self.user)

                # Send email notification to new address
                self.send_email(self.user.email, 
                                'email_subject.html', 
                                'email_email_changed.html', 
                                subject_type = 'email_changed', 
                                username = self.user.name, 
                                user_email = self.user.email)
                
                # Render page with message that email was sent
                state = self.make_state()
                self.render('change_email.html', 
                            user = self.user, 
                            success_message = True,
                            state = state)
        else:
            # Prompt user to login.
            self.render('message.html', message_user_settings_1 = True)


class ChangeUsernameHandler(Handler):

    def get(self):
        if self.user:
            state = self.make_state()
            self.render('change_username.html',
                        user = self.user,
                        state = state)
        else:
            # Prompt user to login.
            self.render('message.html', 
                        message_user_settings_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            # Get user input
            input_username = self.request.get('username')

            # Check input and set error messages. 
            error_username=""
            error_username_exists=""

            have_error = False

            if not valid_username(input_username):
                # Set the error-message: not a valid username.
                error_username = True
                have_error = True

            if have_error == False:
                u = User.by_name(input_username)
                if u:
                    # Set the error-message: username already taken.
                    error_username_exists = True
                    have_error = True
 
            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('change_username.html',
                            user = self.user,
                            username = input_username,
                            error_username = error_username,
                            error_username_exists = error_username_exists,
                            state = state)
            else:
                # Store new username in DB
                self.user.name = input_username
                self.user.put()
                # Update memcache
                User.update_user_cache(self.user)

                # Render page success message
                state = self.make_state()
                self.render('change_username.html', 
                            user = self.user, 
                            success_message = True,
                            state = state)

        else:
            # Prompt user to login.
            self.render('message.html', message_user_settings_1 = True)


class DeleteAccountHandler(Handler):

    def get(self):
        if self.user:
            state = self.make_state()
            self.render('delete_account.html',
                        user = self.user,
                        state = state)
        else:
            # Prompt user to login.
            self.render('message.html', 
                        message_user_settings_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            # Get user input
            input_password = self.request.get('password')

            # Check input and set error messages. 
            error_password=""

            have_error = False

            if not valid_pw(self.user.email, input_password, self.user.pw_hash):
                # Set the error-message: incorrect password.
                error_password = True
                have_error = True

            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('delete_account.html',
                            user = self.user,
                            error_password = error_password,
                            state = state)
            else:
                # Deactivate account by deleting from User database and 
                # adding to the DeactAccounts database.
                d = DeactAccounts.create(self.user.key().id(), 
                                         self.user.name,
                                         self.user.email)
                d.put()

                # Delete user
                User.remove(self.user.key().id())

                # Genrate list of article-keys for the deleted user.
                article_key_list = Article.keys_by_author(self.user.key().id())

                for key in article_key_list:
                    # Store article in DeletdArticle DB
                    article = Article.by_id(key.id())
                    del_art = DeletdArticle.create(article.title,
                                                   article.body, 
                                                   article.author)
                    del_art.put()
                    # Delete article from Article DB
                    Article.remove(key.id())
                
                # Logout (delete coockie)
                self.logout()

                # Send email notification
                self.send_email(d.email, 
                                'email_subject.html', 
                                'email_account_deleted.html', 
                                subject_type = 'account_deleted')


                # Render page with message that account was deleted
                self.render('message.html', 
                            message_delete_account_1 = True, 
                            deleted_email = d.email)

        else:
            # Prompt user to login.
            self.render('message.html', message_user_settings_1 = True)


