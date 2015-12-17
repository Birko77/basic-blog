Basic Blog

This is a basic blog bulit as a web-app on Google App Engine. It has the following features:

1. A basic user administration:
        Login with email and password
        Posibility to reset a forgotten password
        User account settings: Change password, change email, change username, delete account

2. Logged in users can publish and edit articles.

3. Users can contact the website administrator via online form

4. Option to share the website via: email(only logged in), Twitter and Facebook

5. Pages for Privacy policy and Terms of use are included.

User experience:
The wbsite has a responsive design to look nice across different devices and screen sizes. 
After every user action feedback is given via message flashing or info-screens.
Validation of user input on the client side.

Security:
Validation of user input on the server side befor any data processing.
Passwords are stored securely.
SSL connection is used when a user logs in and during the session.
Protection against Cross-Site Request Forgery.

Technology:
Backend: Python, Google App Engine
Web framework: webapp2
Templating language: Jinja2
Data storage: Google Datastore (non SQL)
Frontend framework: Bootstrap
Optimized with memcache to save resources

To run this webapp locally you need to do the following:
1. Create a local clone of this repository on your computer.
2. Download and install Google App Engine SDK for Python.
    https://cloud.google.com/appengine/downloads
3. Open the Google App Engine Launcher and import the app.
    a. Klick on "Add Existing Application..." in the "File" menu.
    b. Navigate to the folder where the "app.yaml" and the .py-files are located.
    c. Klick od "Add" to import the the app.
4. Run the app.
    a. Select the app in the list on the main screen and klick on "Run".
    b. Open a web browser and go to localhost:8080.
        The port-number may vary, it is  given on the main screen of the Google App Engine Launcher.
If locally run, the email functionallity will not work.

To get the app online do the following:
1. Create a Google account.
2. Go the Google Developers console, create a new project and get the Project-ID.
3. Add the Project-ID to the app.yaml file.
    First line: "application: ADD-YOUR-PROJECT-ID-HERE"
4. Edit "sender_address" in the send_email method in the handler.py file.
    You can use the email address of your Google Account,
    or add other emails in the Permissions section of Google Developers Console.
5. Edit "sender" in the ContactHandler class in the homepage-handler.py file.
    You can use the email address of your Google Account,
    or add other emails in the Permissions section of Google Developers Console.

