import cherrypy
import hashlib
import json
import sys


from cr.db.store import global_settings as settings
from cr.db.store import connect
from cr.db.store import global_db as db


SESSION_KEY = 'user'
main = None


def user_verify(username, password):
    """
    Simply checks if a user with provided email and pass exists in db
    :param username: User email
    :param password:  User pass
    :return: True if user found
    """
    users = main.db.users
    user = users.find_one({"email": username})
    password = hashlib.sha1(password.encode()).hexdigest()
    return password == user['hash']


def protect(*args, **kwargs):
    """
    Just a hook for checking protected resources
    :param args:
    :param kwargs:
    :return: 401 if unauthenticated access found (based on session id)
    """
    authenticated = False
    # Check if provided endpoint requires authentication
    condition = cherrypy.request.config.get('auth.require', None)
    if condition is not None:
        try:
            # Try to get the current session
            cherrypy.session[SESSION_KEY]
            # cherrypy.session.regenerate()
            cherrypy.request.login = cherrypy.session[SESSION_KEY]
            # TODO: Should we check if cookie session ID matches the one stored here?
            authenticated = True
        # If there is no session yet, simply redirect to index page
        except KeyError:
            cherrypy.HTTPError(401, u'Not authorized to access this resource. Please login.')

# Specify the hook
cherrypy.tools.crunch = cherrypy.Tool('before_handler', protect)


class Root(object):

    def __init__(self, db_settings):
        self.db = connect(db_settings)

    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True, 'tools.crunch.on': False})
    def index(self):
        import ipdb; ipdb.set_trace()
        # If authenticated, return to users view
        if SESSION_KEY in cherrypy.session:
            raise cherrypy.HTTPRedirect(u'/users', status=301)
        else:
            return 'Welcome to Crunch.  Please <a href="/login">login</a>.'


    @cherrypy.tools.allow(methods=['GET', 'POST'])
    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True})
    # @require
    def users(self, *args, **kwargs):
        """
        for GET: update this to return a json stream defining a listing of the users
        for POST: should add a new user to the users collection, with validation

        Only logged-in users should be able to connect.  If not logged in, should return the
        appropriate HTTP response.  Password information should not be revealed.

        note: Always return the appropriate response for the action requested.
        """
        import ipdb; ipdb.set_trace()
        if cherrypy.request.method == 'GET':
            return json.dumps({'users': [u for u in self.db.users.find()]})
        elif cherrypy.request.method == 'POST':
            # Get post form data and create a new user
            user = cherrypy.request.json
            return user


    @cherrypy.tools.allow(methods=['GET', 'POST'])
    @cherrypy.expose
    @cherrypy.config(**{'tools.crunch.on': False})
    def login(self, *args, **kwargs):
        """
        a GET to this endpoint should provide the user login/logout capabilities

        a POST to this endpoint with credentials should set up persistence tokens for the user,
        allowing them to access other pages.

        hint: this is how the admin's password was generated:
              import hashlib; hashlib.sha1('123456').hexdigest()
        """
        import ipdb; ipdb.set_trace()
        if cherrypy.request.method == 'GET':
            # Check if user is logged in already
            if SESSION_KEY in cherrypy.session:
                return """<html>
                  <head></head>
                  <body>
                    <form method="post" action="logout">
                      <label>Click button to logout</label>
                      <button type="submit">Logout</button>
                    </form>
                  </body>
                </html>"""

            else:
                return """<html>
                  <head></head>
                  <body>
                    <form method="post" action="login">
                      <input type="text" value="Enter email" name="username" />
                      <input type="password" value="Enter password" name="password" />
                      <button type="submit">Login</button>
                    </form>
                  </body>
                </html>"""
        elif cherrypy.request.method == 'POST':
            # Get post form data and create a new user
            if 'password' and 'username' in kwargs:
                user = kwargs['username']
                password = kwargs['password']
                if user_verify(user, password):
                    # FIXME: Not sure if this is needed, in theory Cherrypy recreates session if cookie ID != session ID
                    cherrypy.session.regenerate()
                    cherrypy.session[SESSION_KEY] = cherrypy.request.login = user
                    # Redirect to users
                    raise cherrypy.HTTPRedirect(u'/users', status=301)
                else:
                    raise cherrypy.HTTPError(u'401 Unauthorized')


    @cherrypy.tools.allow(methods=['GET'])
    @cherrypy.expose
    def logout(self):
        """
        Should log the user out, rendering them incapable of accessing the users endpoint, but
        """

    @cherrypy.expose
    def distances(self):
        """
        Each user has a lat/lon associated with them.  Using only numpy, determine the distance
        between each user pair, and provide the min/max/average/std as a json response.
        This should be GET only.

        Don't code, but explain how would you scale this to 1,000,000 users, considering users
        changing position every few minutes?
        """

if __name__ == '__main__':
    config_root = {'/': {
        'tools.crunch.on': True,
        'tools.sessions.on': True,
        'tools.sessions.name': 'crunch', }
    }
    settings.update(json.load(open(sys.argv[1])))
    main = Root(settings)
    cherrypy.quickstart(main, '/', config=config_root)