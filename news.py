import cgi, os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from datetime import timedelta, datetime
import urllib2, math
#from google.appengine.api import memcache
#http://code.google.com/appengine/docs/python/memcache/usingmemcache.html#Memcache

class Entry(polymodel.PolyModel): 
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)
    ups = db.IntegerProperty()

# Hack moche pour simuler un cron
test_cron = Entry.all()
test_cron.filter('content = ', 'FC')
if test_cron.count():
    cron = Entry.get(test_cron.fetch(1)[0].key())
else:
    cron = Entry()
    cron.content = "FC"
    cron.put()

class Post(Entry):
    url = db.StringProperty()
    site = db.StringProperty()
    rank = db.IntegerProperty()

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

def user_found(u, e):
# return 0 is not found and 1 if found #
    v = Up.all()
    v.filter('entry =', Entry.get(e))
    v.filter('voter =', u)
    return v.count()

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

class MainPage(webapp.RequestHandler):
    def get(self):
        if calc_minutes(cron) > 19:
            cron.date = datetime.utcnow()
            cron.put()
            posts_query = Post.all()
            posts = posts_query.fetch(80) # HARDCODED LIMIT
            for post in posts:
                post.rank = update_rank(post)
                post.put()
        posts_query = Post.all().order('-rank')
        posts = posts_query.fetch(20)
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'posts': DisplayPosts(posts, users.get_current_user()),
            'url': url,
            'url_linktext': url_linktext,
            'submit': '/submit',
            'submit_linktext': 'Submit',
            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Submit(webapp.RequestHandler):
    @login_required     # Only work for get()
    def get(self):
        template_values = {
                }
        path = os.path.join(os.path.dirname(__file__), 'submit.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        submit = Post()
        if users.get_current_user():
            submit.author = users.get_current_user()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        submit.url = self.request.get('url')
        # Already submited ? 
        test = Post.all()
        test.filter("url = ", submit.url)
        res = test.fetch(1)
        if res:
            self.redirect('/already_submitted')
            return -1
        # Browsable ?
        try:
            urllib2.urlopen(submit.url)
        except:
            self.redirect('/wrong_submit')
            return -1
        if self.request.get('content'):
            submit.content = self.request.get('content')
        else:
            print
            print 'Comment tu veux que je fasse un lien sur la chaine vide ? Empty string !'
            return -1

        submit.site = submit.url.split('/')[2] # should be a regexp ? 
        submit.rank = 0
        submit.ups = 0
        submit.put()
        self.redirect('/')
        return 0

class ViewComment(webapp.RequestHandler):
    def get(self):
        com = Comment.all()
        post = Post.get_by_id(int(self.request.get('pid')))
        com.filter('post =', post)
        # TODO Reply => recursively descend
        com.order('date')
        comments = com.fetch(5000) # hardcoded limit
        if users.get_current_user() is None:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            template_values = {
                    'post': post,
                    'url': url,
                    'url_linktext': url_linktext,
                    'comments': DisplayComments(comments, None),
                    'view': 0
                    }
        else:
            template_values = {
                    'post': post,
                    'comments': DisplayComments(comments, users.get_current_user()),
                    'view': 1 - user_found(users.get_current_user(), post.key())
                    }
        path = os.path.join(os.path.dirname(__file__), 'comment.html')
        self.response.out.write(template.render(path, template_values))
    def post(self):
        submit = Comment()
        if users.get_current_user():
            submit.author = users.get_current_user()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        submit.content = self.request.get('content')
        pid = self.request.get('pid')
        submit.post = Post.get_by_id(int(pid))
        submit.ups = 0
        submit.put()
        self.redirect('/comment?pid=' + pid)

class Vote(webapp.RequestHandler):
    @login_required     # Only work for get()
    def get(self):
        e = Post.get_by_id(int(self.request.get('for')))
        if (user_found(users.get_current_user(), e.key())):
            return -1
        v = Up()
        v.voter = users.get_current_user()
        v.entry = e
        v.put()
        e.ups = e.ups + 1
        if (e.__class__.__name__ == "Post"):
            e.rank = update_rank(e)
        e.put()

# Never finish any code or you'll get old ...
class WrongSubmit(webapp.RequestHandler):
    def get(self):
        print 
        print "ton URL n'est pas browsable par mon urllib2 !"

class AlreadySubmitted(webapp.RequestHandler):
    def get(self):
        print 
        print "ton URL est deja dans la DB !"

application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/vote', Vote),
                                     ('/submit', Submit),
                                     ('/comment', ViewComment),
                                     ('/wrong_submit', WrongSubmit),
                                     ('/already_submitted', AlreadySubmitted)],
                                    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

