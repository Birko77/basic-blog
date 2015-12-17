import webapp2
from webapp2_extras import sessions
import jinja2
import os
import logging

from utils import *
from user_database import User

from google.appengine.api import mail

# Create an instance of the Jinja2.environment class to
# load the templates from the filesystem.
# Use the Jinja2 builtin FileSystemLoader().
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                       autoescape = True)


# The following Handler-class will be inherited 
# by every request handler class.

class Handler(webapp2.RequestHandler):

# --- RENDERING ---

    def write(self, *a, **kw):
        '''Write to the body fo the response-object

        Arguments:
        *a, **kw -- here the response body created by render_str()
        '''
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        '''Render a template with the given parameters

        Load the template by calling the get_template() method
        Render the template by calling the render() method and passing
        the params to it.
        Arguments:
        template -- the name of the template-file
        **params -- the variables to be passed to the renderer
        Return value:
        the redered template
        '''
        template_params = params
        t = jinja_environment.get_template(template)
        return t.render(template_params)

    def render(self, template, **kw):
        '''Create a response-body 

        Render a given template and write the result to the 
        response body.
        Arguments:
        template -- name of the template-file
        **kw -- the variables to be passed to the renderer
        '''
        self.write(self.render_str(template, **kw))


# --- COOKIE HANDLING ---

    def set_secure_cookie(self, name, val):
        '''Set a cookie with a hashed value

        Create a hashed value by calling the make_secure_val() method.
        Add a cookie header to the response-object.
        Arguments:
        name -- name of the cookie
        val -- value to generate the hashed value for the cookie
        '''
        cookie_val = str(make_secure_val(val))
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        '''Read a cookie with a hashed value

        Check if a cookie with the name 'name' is sent with the request.
        If yes, check the hashed value and return the unhashed value.
        Argument:
        name -- name of the cookie
        Return value:
        None or '' -- if the cookie does not exist or the hashed value 
        does not pass check_secure_val().
        The unhashed value of the cookie -- if check_secure_val() is passed.
        '''
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
        # https://docs.python.org/2/reference/expressions.html#and
        # The expression x and y first evaluates x; 
        # if x is false, its value is returned; otherwise, 
        # y is evaluated and the resulting value is returned.


# --- LOGIN, LOGOUT ---

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')


# --- SECURITY AGAINST CSRF ---

    def make_state(self):
        ''' Make a random state-token, set a cookie and return the token.

        Return value:
        state -- state-token
        '''
        state = ''.join(random.choice(string.ascii_uppercase 
            + string.digits) for x in xrange(32))
        self.set_secure_cookie('state', state)
        return state

    def check_state(self):
        ''' Compare the state-values from cookie and form.
        
        Get the value of 'state' from the form. 
        Get the value of the state-cookie by calling read_secure_cookie().
        Conmpare the two values and return the result.
        Log a warning if the two values are not the same.
        Return values:
        True if the two values are the same. 
        False if the two values are not the same.
        '''
        input_state_form = self.request.get('state')
        input_state_cookie = self.read_secure_cookie('state')
        self.response.headers.add_header('Set-Cookie', 'state=; Path=/')
        if input_state_cookie and (input_state_cookie == input_state_form):
            return True
        else:
            logging.warning("Possible CSRF attack detected!")
            return False


# --- INITIALIZE ---

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        # Initialize() is called after every request.
        # self.user is either set to None (if there is no user_id-cookie)
        # or to the entity returned from the Datastore (possibly None)

# --- EMAIL HANDLING ---

    def send_email(self, to_address, subject_template, email_template, **kw):
        '''Send an email

        Check if the given email address is valid.
        If not valid, log warning.
        If valid, send email.
        Arguments:
        to_address -- receiver email address
        subject_template -- name of template file for the email subject
        email_template -- name of template file for the email body
        **kw -- vriables to be passed to the templates
        '''
        if not mail.is_email_valid(to_address):
            logging.warning('Invalid email address was given by user.')

        else:
            # Set the following sender_address to a valid GAE admin address 
            sender_address = "Blog <blog@gmail.com>"
            body = self.render_str(email_template, **kw)
            subject = self.render_str(subject_template, **kw)
            mail.send_mail(sender_address, to_address, subject, body)

#--- EXCEPTIONS ---

    def handle_exception(self, exception, debug_mode):
        if debug_mode:
            webapp2.RequestHandler.handle_exception(self, exception, debug_mode)
        else:
            logging.exception(exception)
            self.error(500)
            self.render('error.html')


