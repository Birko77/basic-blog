"""Datastore models for blog articles and comments 

Classes:
Article -- Model for the Blog articles
Comment -- Model for Comments 
"""

import logging

from google.appengine.ext import db
from google.appengine.api import memcache

from utils import *


class Article(db.Model):
    """Datastore model for the Blog articles

    Methods:
    by_id -- Return an Article-object for a given article-id.
    remove -- 
    """

    title = db.StringProperty(required = True)
    body = db.TextProperty(required = True)
    author = db.IntegerProperty(required = True) #user-id of author
    created = db.DateTimeProperty(auto_now=True)

    @classmethod
    def by_id(cls, article_id):
        """Return an Article-object for a given Article-id

        Read first from memcache. If Article-object is not stored in memcache, 
        execute a Datastore query and update memcache.
        Return None if entity is not found.
        Argument:
        article_id -- the Article-id, this is the Datastore entity's key
        Return value:
        article -- the Article-object for the given article-id, None if not found
        """

        key = str(article_id)
        article = memcache.get(key)
        if article is None:
            article = Article.get_by_id(int(article_id))
            memcache.set(key, article)
        return article

    @classmethod
    def update_article_cache(cls, article):
        """Store an Article-object in memcache.

        Store an Article-object in memcache. The key is the Article-id .
        Argument:
        article -- the Article-object to be stored in memcache
        """

        key = str(article.key().id())
        memcache.set(key, article)

    @classmethod
    def keys_by_author(cls, author):
        """Return a list of Article-keys for a given author-id.

        Execute a Datastore keys-only query and filter by the given author-id.
        Return the list of entity keys.
        
        Argument:
        author -- the user-id of the author
        Return value:
        key_list -- list of entity keys for the given author, None if not found
        """
        key_list = Article.all(keys_only=True).filter("author", int(author))
        return key_list

    @classmethod
    def by_author(cls, author):
        """Return a list of Article-objects for a given author-id.

        Create a list of article-keys by calling the keys_by_author() method..
        Create a list of article-objects by calling the by_id() method for
        every key.

        Argument:
        author -- the user-id of the author
        Return value:
        article_list -- list of Article-objects for the given author
        Returns an empty list if no entity is found.
        """
        key_list = cls.keys_by_author(author)
        article_list = []
        for key in key_list:
            article = cls.by_id(key.id())
            article_list.append(article)
        return article_list

    @classmethod
    def recent(cls, number):
        """Return a list of the most recent Article-objects.

        Argument:
        number -- the number of articles in the list
        Return value:
        article_list -- list of Article-objectsr
        Returns an empty list if no entity is found.
        """
        key_list = Article.all(keys_only=True).order('-created')
        article_list = []
        for key in key_list.run(limit = int(number)):
            article = cls.by_id(key.id())
            article_list.append(article)
        return article_list


    @classmethod
    def create(cls, title, body, author):
        """Return a new Article-object to store in the datastore.

        Construct and return a new Article-object with the given arguments.
        Arguments:
        title -- the title of the article
        body -- the body of the article
        author -- the user-id of the author of the article
        Return value:
        article -- the new Article-object
        """

        return Article(title = title,
                       body = body,
                       author = author)

   
    @classmethod
    def remove(cls, article_id):
        """Delete an Article-object from the datastore.

        Delete Article-object from datastore and memcache.
        Argument:
        article_id -- Article-id
        """
        article = Article.by_id(int(article_id))
        db.delete(article)

        key = str(article_id)
        memcache.delete(key)


class DeletdArticle(db.Model):
    """Datastore model for the DeletdArticle-Objects.

    The stored entities represent deleted articles.
    Methods:
    create -- Return a new DeletdArticle-object.
    """

    title = db.StringProperty(required = True)
    body = db.TextProperty(required = True)
    author = db.IntegerProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def create(cls, title, body, author):
        """Return a new DeactAccounts-object.

        Construct and return a new DeactAccounts-object with the given 
        arguments.
        Arguments:
        title -- the title of the article [string]
        body -- the body of the article [string]
        author -- the user-id of the author of the article [integer]
        Return value:
        the new DeactAccounts-object
        """

        return DeletdArticle(title = title, body = body, author = int(author))


