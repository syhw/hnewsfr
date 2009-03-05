import math
from google.appengine.ext import db
from datetime import timedelta, datetime
from google.appengine.ext.db import polymodel

#from google.appengine.api import memcache
#http://code.google.com/appengine/docs/python/memcache/usingmemcache.html#Memcache

class Entry(polymodel.PolyModel): 
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)
    ups = db.IntegerProperty()

posts_limit = 800 # Hardcoded limit
comments_limit = 400 # Hardcoded limit
# Hack moche pour simuler un cron
test_cron = Entry.all()
test_cron.filter('content = ', 'FC')
if test_cron.count(): # is_saved()
    cron = Entry.get(test_cron.fetch(1)[0].key())
else:
    cron = Entry()
    cron.content = "FC"
    cron.put()

class Post(Entry):
    url = db.StringProperty()
    site = db.StringProperty()
    rank = db.IntegerProperty()
    def get_comments(self):
        com = Comment.all()
        com.filter('post =', self)
        # TODO Reply => recursively descend
        com.order('-ups')
        return com.fetch(comments_limit)

class Comment(Entry):
    post = db.ReferenceProperty(Entry)

class Up(db.Model):
    entry = db.ReferenceProperty(Entry)
    voter = db.UserProperty()

def calc_hours(post):
    diff = datetime.utcnow() - post.date
    hours = diff.seconds/3600  # :)
    if diff.days is not -1:
        hours = hours + diff.days*24
    return hours

def calc_minutes(post):
    diff = datetime.utcnow() - post.date
    minutes = diff.seconds/60  # :]
    if diff.days is not -1:
        minutes = minutes + diff.days*24
    return minutes

def count_comments(key):
    c = Comment.all()
    c.filter('post =', Post.get(key))
    return c.count() 

#def count_comments(post):
#    c = Comment.all()
#    c.filter('post =', post)
#    return c.count()

def update_rank(post):
    #post.rank = (3*post.ups + count_comments(post)) / (4*calc_hours(post) + 1)
    return int(math.ceil(post.ups / math.pow(calc_hours(post) + 1, 1.5)))

def update_ranks():
    posts_query = Post.all()
    posts = posts_query.fetch(posts_limit) 
    for post in posts:
        post.rank = update_rank(post)
        post.put()
    return 0

def update_check():
    if calc_minutes(cron) > 19:
        cron.date = datetime.utcnow()
        cron.put()
        update_ranks()

def user_found(u, e):
# return 0 is not found and 1 if found #
    v = Up.all()
    v.filter('entry =', Entry.get(e))
    v.filter('voter =', u)
    return v.count()

def already(url):
    test = Post.all()
    test.filter("url = ", url)
    return test.fetch(1)

class DisplayPost(Post):
    def __init__(self, post, u):
        self.hours = calc_hours(post)
        self.minutes = calc_minutes(post)
        self.comments_number = count_comments(post.key())
        self.author = post.author
        self.content = post.content
        self.ups = post.ups
        self.url = post.url
        self.site = post.site
        self.id = (post.key()).id
        if (u is None):
            self.varw = 0
        else:
            self.varw = 1 - user_found(u, post.key())

class DisplayPosts(list):
    def __init__(self, posts, u):
        for post in posts:
            self.append(DisplayPost(post, u))

class DisplayComment(Comment):
    def __init__(self, com, u):
        self.hours = calc_hours(com)
        self.minutes = calc_minutes(com)
        # self.comments_number = TODO
        self.author = com.author
        self.content = com.content
        self.ups = com.ups
        self.id = (com.key()).id
        if (u is None):
            self.varw = 0
        else:
            self.varw = 1 - user_found(u, com.key())

class DisplayComments(list):
    def __init__(self, comments, u):
        for c in comments:
            self.append(DisplayComment(c, u))

class FeedPost(Post):
    def __init__(self, post):
        self.content = post.content
        self.ups = post.ups
        self.url = post.url
        self.site = post.site
        self.fdate = post.date.strftime("%Y-%m-%dT%H:%M:%SZ")

class FeedPosts(list):
    def __init__(self, posts):
        for post in posts:
            self.append(FeedPost(post))

