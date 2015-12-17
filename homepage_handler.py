import time
import logging

from handler import Handler

from google.appengine.api import mail

from utils import *
from article_database import Article
from user_database import User

class HomePageHandler(Handler):
    def get(self):
        article_list = Article.recent(100)
        for article in article_list:
            t = article.created.isoformat()
            article.time = t
            author = User.by_id(article.author)
            if author:
                article.author_name = author.name
            else:
                article.author_name = 'Unknown'

        if self.user:
            self.render('homepage.html',
                        user = self.user, 
                        article_list = article_list)
        else:
            self.render('homepage.html', article_list = article_list)


class NewArticleHandler(Handler):
    def get(self):
        if self.user:
            state = self.make_state()
            self.render('new_article.html', user = self.user, state = state)
        else:
            # Prompt user to login.
            self.render('message.html', message_new_article_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            input_title = self.request.get('title')
            input_body = self.request.get('body')

            error_title=""
            error_body=""

            have_error = False

            if not valid_title(input_title):
                # Show the error-message: not a valid title.
                error_title = True
                have_error = True
            if not valid_body(input_body):
                # Show the error-message: not a valid body.
                error_body = True
                have_error = True

            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('new_article.html',
                            user = self.user,
                            error_title = error_title,
                            error_body = error_body,
                            title_form = input_title,
                            body_form = input_body,
                            state = state)
            else:
                # Create new entry in the Article-DB.
                article = Article.create(input_title, 
                                         input_body, 
                                         self.user.key().id())
                article.put()
                # Update memcache
                Article.update_article_cache(article)
                
                # Redirect to homepage
                self.redirect("/")

        else:
            # Prompt user to login.
            self.render('message.html', message_new_article_1 = True)



class EditArticleHandler(Handler):
    def get(self):
        if self.user:
            input_article_id = self.request.get("article")
            article = Article.get_by_id(int(input_article_id))
            if self.user.key().id() == article.author:
                state = self.make_state()
                self.render('edit_article.html', 
                            user = self.user,  
                            article = article, 
                            title_form = article.title, 
                            body_form = article.body,
                            state = state)
            else:
                # Show message that user is not authorized to edit.
                self.render('message.html', message_edit_article_2 = True)
        else:
            # Prompt user to login.
            self.render('message.html', message_edit_article_1 = True)

    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            input_delete_article = self.request.get('delete_article')

            if input_delete_article:
                Article.remove(input_delete_article)
                # Show message: Confirm deletion of article.
                self.render('message.html', message_delete_article = True)

            else:
                input_edit_article = self.request.get('edit_article')
                input_title = self.request.get('title')
                input_body = self.request.get('body')

                article = Article.by_id(input_edit_article)
                
                error_title=""
                error_body=""

                have_error = False

                if not valid_title(input_title):
                    # Show the error-message: not a valid title.
                    error_title = True
                    have_error = True
                if not valid_body(input_body):
                    # Show the error-message: not a valid body.
                    error_body = True
                    have_error = True

                if have_error:
                    state = self.make_state()
                    # Render page with error-messages.
                    self.render('edit_article.html',
                                user = self.user,
                                article = article,
                                error_title = error_title,
                                error_body = error_body,
                                title_form = input_title,
                                body_form = input_body,
                                state = state)
                else:
                    # Edit article-entity and commit to Article-DB.
                    article.title = input_title
                    article.body = input_body
                    article.put()
                    # Update memcache
                    Article.update_article_cache(article)
                    # Redirect to homepage
                    self.redirect("/")

        else:
            # Prompt user to login.
            self.render('message.html', message_new_article_1 = True)



class ContactHandler(Handler):
    def get(self):
        if self.user:
            state = self.make_state()
            self.render('contact.html', 
                        user = self.user, 
                        email_form = self.user.email,
                        state = state)
        else:
            state = self.make_state()
            self.render('contact.html',
                        state = state)

    def post(self):
        if not self.check_state():
            logging.warning("Possible CSRF attack detected!")
            self.redirect("/")
            return

        input_email = self.request.get('email')
        input_subject = self.request.get('subject')
        input_content = self.request.get('content')

        error_email=""
        error_subject=""
        error_content=""

        have_error = False

        if not valid_email(input_email):
            # Show the error-message: not a valid email.
            error_email = True
            have_error = True
        if not valid_subject(input_subject):
            # Show the error-message: not a valid subject.
            error_subject = True
            have_error = True
        if not valid_content(input_content):
            # Show the error-message: not a valid content.
            error_content = True
            have_error = True

        if have_error:
            if self.user:
                state = self.make_state()
                # Render page with error-messages.
                self.render('contact.html',
                            error_email = error_email,
                            error_subject = error_subject,
                            error_content = error_content,
                            email_form = input_email,
                            subject_form = input_subject,
                            content_form = input_content,
                            user = self.user,
                            state = state)
            else:
                state = self.make_state()
                # Render page with error-messages.
                self.render('contact.html',
                            error_email = error_email,
                            error_subject = error_subject,
                            error_content = error_content,
                            email_form = input_email,
                            subject_form = input_subject,
                            content_form = input_content,
                            state = state)

        else:
            if self.user:
                state = self.make_state()
                # Render page with success-message.
                self.render('contact.html', 
                            success_message = True, 
                            user = self.user, 
                            email_form = self.user.email,
                            state = state)
            else:
                state = self.make_state()
                # Render page with success-message.
                self.render('contact.html', 
                            success_message = True,
                            state = state)

            # Send email to administrator
            # Set the following sender to a valid GAE admin address
            sender = "blog@gmail.com"
            subject = input_subject
            body = "Message from: "+input_email+" --- Content: "+input_content
            mail.send_mail_to_admins(sender, subject, body)


class AboutHandler(Handler):
    def get(self):
        if self.user:
            self.render('about.html', user = self.user)
        else:
            self.render('about.html')


class TermsHandler(Handler):
    def get(self):
        if self.user:
            self.render('terms.html', user = self.user)
        else:
            self.render('terms.html')


class PrivacyHandler(Handler):
    def get(self):
        if self.user:
            self.render('privacy.html', user = self.user)
        else:
            self.render('privacy.html')


class SendEmailHandler(Handler):

    def get(self):
        if self.user:
            state = self.make_state()
            self.render('send_email.html', 
                        user = self.user, 
                        email_from_form = self.user.email,
                        state = state)
        else:
            self.render('send_email.html', error_no_user = True)


    def post(self):
        if self.user:
            if not self.check_state():
                logging.warning("Possible CSRF attack detected!")
                self.redirect("/")
                return

            input_email_to = self.request.get('email_to')
            input_email_from = self.request.get('email_from')
            input_content = self.request.get('content')

            error_email_to=""
            error_email_from=""
            error_content=""

            have_error = False

            if not valid_email(input_email_to):
                # Show the error-message: not a valid email.
                error_email_to = True
                have_error = True
            if not valid_email(input_email_from):
                # Show the error-message: not a valid email.
                error_email_to = True
                have_error = True
            if not valid_content(input_content):
                # Show the error-message: not a valid content.
                error_content = True
                have_error = True

            if have_error:
                state = self.make_state()
                # Render page with error-messages.
                self.render('send_email.html',
                            error_email_to = error_email_to,
                            error_email_from = error_email_from,
                            error_content = error_content,
                            email_to_form = input_email_to,
                            email_from_form = input_email_from,
                            content_form = input_content,
                            user = self.user,
                            state = state)

            else:
                state = self.make_state()
                # Render page with success-message.
                self.render('send_email.html', 
                            success_message = True, 
                            sent_email = input_email_to, 
                            email_from_form = self.user.email, 
                            user = self.user,
                            state = state)

                # Send email.
                self.send_email(input_email_to, 
                                'email_subject.html', 
                                'email_recommend_joe.html', 
                                subject_type = 'recommend_joe', 
                                content = input_content, 
                                sender = input_email_from)


        else:
            # Prompt user to login.
            self.render('message.html', message_send_email_1 = True)

