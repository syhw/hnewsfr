import cgi, os, data, urllib2
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.util import login_required

class MainPage(webapp.RequestHandler):
    def get(self):
        posts_query = data.Post.all().order('-rank')
        posts = posts_query.fetch(20)
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'posts': data.DisplayPosts(posts, users.get_current_user()),
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
        submit = data.Post()
        if users.get_current_user():
            submit.author = users.get_current_user()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        submit.url = self.request.get('url')
        # Already submited ? 
        if data.already(submit.url):
            self.redirect('/already_submitted')
            return -1
        # Browsable ?
        try:
            urllib2.urlopen(submit.url)
        except:
            self.redirect('/wrong_submit')
            return -1
        # Non-empty content
        if self.request.get('content'):
            submit.content = self.request.get('content')
        else:
            self.redirect('/empty_content')
            return -1
        submit.site = submit.url.split('/')[2] # should be a regexp ? 
        submit.rank = 0
        submit.ups = 0
        submit.put()
        data.update_ranks()
        self.redirect('/')
        return 0

class ViewComment(webapp.RequestHandler):
    def get(self):
        post = data.Post.get_by_id(int(self.request.get('pid')))
        if users.get_current_user() is None:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            template_values = {
                    'post': data.DisplayPost(post, None),
                    'url': url,
                    'url_linktext': url_linktext,
                    'comments': data.DisplayComments(post.get_comments(), None),
                    'view': 0
                    }
        else:
            u = users.get_current_user()
            template_values = {
                    'post': data.DisplayPost(post, u),
                    'comments': data.DisplayComments(post.get_comments(), u),
                    'view': 1 - data.user_found(u, post.key())
                    }
        path = os.path.join(os.path.dirname(__file__), 'comment.html')
        self.response.out.write(template.render(path, template_values))
    def post(self):
        submit = data.Comment()
        if users.get_current_user():
            submit.author = users.get_current_user()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        submit.content = self.request.get('content')
        pid = self.request.get('pid')
        submit.post = data.Post.get_by_id(int(pid))
        submit.ups = 0
        submit.put()
        self.redirect('/comment?pid=' + pid)
        return 0

class Vote(webapp.RequestHandler):
    @login_required     # Only work for get()
    def get(self):
        e = data.Post.get_by_id(int(self.request.get('for')))
        if (data.user_found(users.get_current_user(), e.key())):
            return -1
        v = data.Up()
        v.voter = users.get_current_user()
        v.entry = e
        v.put()
        e.ups = e.ups + 1
        e.put()
        if (e.__class__.__name__ == "Post"):
            data.update_ranks()
        else:
            data.update_comments()

class RSS(webapp.RequestHandler):
    def get(self):
        data.update_check()
        posts_query = data.Post.all().order('-rank')
        posts = posts_query.fetch(6)
        template_values = {
            'posts': data.FeedPosts(posts),
            }
        path = os.path.join(os.path.dirname(__file__), 'news.xml')
        self.response.headers["Content-Type"] = "application/rss+xml; charset=utf-8"
        self.response.out.write(template.render(path, template_values))

# Never finish any code or you'll get old ...
class WrongSubmit(webapp.RequestHandler):
    def get(self):
        print 
        print "ton URL n'est pas browsable par mon urllib2 !"

class AlreadySubmitted(webapp.RequestHandler):
    def get(self):
        print 
        print "ton URL est deja dans la DB !"

class EmptyContent(webapp.RequestHandler):
    def get(self):
        print
        print 'Comment tu veux que je fasse un lien sur la chaine vide ? Empty string !'

application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/rss', RSS),
                                     ('/vote', Vote),
                                     ('/submit', Submit),
                                     ('/comment', ViewComment),
                                     ('/wrong_submit', WrongSubmit),
                                     ('/empty_content', EmptyContent),
                                     ('/already_submitted', AlreadySubmitted)],
                                    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

