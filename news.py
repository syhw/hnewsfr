import cgi, os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from datetime import timedelta, datetime
import urllib2
#from google.appengine.api import memcache
#http://code.google.com/appengine/docs/python/memcache/usingmemcache.html#Memcache

# (p-1)/(t+2)^1.5     p votes   t in hours

class Entry(db.Model): 
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)
    ups = db.IntegerProperty()

class Post(Entry):
    url = db.StringProperty()
    site = db.StringProperty()
    rank = db.IntegerProperty()

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

class DisplayPost(Post):
    def __init__(self, post):
        self.hours = calc_hours(post)
        self.minutes = calc_minutes(post)
        self.comments_number = count_comments(post.key())
        self.author = post.author
        self.content = post.content
        self.ups = post.ups
        self.url = post.url
        self.site = post.site
        self.id = (post.key()).id

class DisplayPosts(list):
    def __init__(self, posts):
        for post in posts:
            self.append(DisplayPost(post))

class Comment(Entry):
    post = db.ReferenceProperty(Entry)

class DisplayComment(Comment):
    def __init__(self, com):
        self.hours = calc_hours(com)
        self.minutes = calc_minutes(com)
        # self.comments_number = TODO
        self.author = com.author
        self.content = com.content
        self.ups = com.ups
        self.id = (com.key()).id

class DisplayComments(list):
    def __init__(self, comments):
        for c in comments:
            self.append(DisplayComment(c))

class MainPage(webapp.RequestHandler):
    def get(self):
        posts_query = Post.all().order('-rank')
        posts = posts_query.fetch(20)
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'posts': DisplayPosts(posts),
            'url': url,
            'url_linktext': url_linktext,
            'submit': '/submit',
            'submit_linktext': 'Submit',
            'user': users.get_current_user()
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
            print 'Comment tu veux que je fasse un lien sur la chaine vide ?'
            print 'Empty string !'
            print ''
            print '                                  ,;;;;;;,'
            print '                                ,;;;`""`;;|'
            print '                              ,;;;/  .```,;|'
            print '                            ,;;;;/   |    ||_'
            print '                           /;;;;;    |    / .|'
            print '                         ,;;;;;;|     `.  |/_/'
            print '                        /;;;;;;;|       |'
            print '             _,.---._  /;;;;;;;;|        ;   _.---.,_'
            print '           .;;/      `.;;;;;;;;;|         ;`      |;;,'
            print '         .;;;/         `;;;;;;;;;.._    .`         |;;;.'
            print '        /;;;;|          _;-"`       `"-;_          |;;;;|'
            print '       |;;;;;|.---.   .`  __.-"```"-.__  `.   .---.|;;;;;|'
            print '       |;;;;;|     `|/  .`/__|     /__|`.  |/`     |;;;;;|'
            print '       |;;;;;|       |_/ //  ||   //  || |_|       |;;;;;|'
            print '       |;;;;;|       |/ |/    || ||    || ||       |;;;;;|'
            print '        |;;;;|    __ || _  .-.|| |/.-.  _ || __    |;;;;/'
            print '         |jgs|   / _||/ = /_o_|   /_o_| = ||/_ |   |;;;/'
            print '          |;;/   |`.-     `   `   `   `     -.`|   |;;/'
            print '         _|;`    | |    _     _   _     _    | /    `;|_'
            print '        / .|      ||_  ( `--`(     )`--` )  _//      /. |'
            print '        |/_/       |_/|  /_   |   |   _|  ||_/       |_|/'
            print '                      | /|||  |   /  //|| |'
            print '                      |  | |`._`-`_.`/ |  |'
            print '                      |  ;  `-.```.-`  ;  |'
            print '                      |   |    ```    /   |'
            print '    __                ;    `.-"""""-.`    ;                __'
            print '   /| |_         __..--|     `-----`     /--..__         _/ /|'
            print '   |_`/|```---```..;;;;.`.__,       ,__.`,;;;;..```---```/|`_/'
            print '        `-.__``;;;;;;;;;;;,,`._   _.`,,;;;;;;;;;;;``__.-`'
            print '             ````--; ;;;;;;;;..`"`..;;;;;;;; ;--````   _'
            print '        .-.       /,;;;;;;;`;;;;;;;;;`;;;;;;;,|    _.-` `|'
            print '      .`  /_     /,;;;;;;`/| ;;;;;;; ||`;;;;;;,|  `|     `-`|'
            print '     /      )   /,;;;;;`,` | ;;;;;;; | `,`;;;;;,|   |   .`-./'
            print '     ``-..-`   /,;;;;`,`   | ;;;;;;; |   `,`;;;;,|   `"`'
            print '              | ;;;`,`     | ;;;;;;; |  ,  `, ;;;`|'
            print '             _|__.-`  .-.  ; ;;;;;;; ;  |`-. `-.__/_'
            print '            / .|     (   )  |`;;;;;`/   |   |    /. |'
            print '            |/_/   (`     `) |`;;;`/    `-._|    |_|/'
            print '                    `-/ |-`   `._.`         `'
            print '                      """      /.`|'
            print '                               ||_/'
            print ''
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
                    'comments': DisplayComments(comments)
                    }
        else:
            template_values = {
                    'post': post,
                    'comments': DisplayComments(comments)
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
        submit.put()
        self.redirect('/comment?pid=' + pid)

# Never finish any code or you'll get old ...
class WrongSubmit(webapp.RequestHandler):
    def get(self):
        print "ton URL n'est pas browsable par mon urllib2 !"

class AlreadySubmitted(webapp.RequestHandler):
    def get(self):
        print "ton URL est deja dans la DB !"

application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/submit', Submit),
                                     ('/comment', ViewComment),
                                     ('/wrong_submit', WrongSubmit),
                                     ('/already_submitted', AlreadySubmitted)],
                                    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

