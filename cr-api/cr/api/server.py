import cherrypy
import hashlib
import json
import sys
import base64
import re

from cr.db.store import global_settings as settings
from cr.db.store import connect
from cr.db.store import global_db as db


# def check_success():
#     return False
#
# def validate_password(realm, username, password):
#     import ipdb; ipdb.set_trace()
#     # Check provided password is valid
#     users = Root.get_db().users
#     user = users.find_one({"email": username})
#     # Check if provided password matches
#     stored_password = hashlib.sha1(user.password.encode()).hexdigest()
#     if password == stored_password:
#         cherrypy.session[SESSION_KEY] = user.email
#         return cherrypy.HTTPRedirect('/users')
#     else:
#         return cherrypy.HTTPError("401 Unauthorized")
#
# def do_redirect():
#     raise cherrypy.HTTPRedirect("/login")
#
# def check_auth(call_func=do_redirect):
#     # do check ...
#     import ipdb; ipdb.set_trace()
#     if check_success():
#         return
#     call_func()
#
# cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth, priority=60)

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
    import ipdb; ipdb.set_trace()
    authenticated = False
    # Check if provided endpoint requires authentication
    condition = cherrypy.request.config.get('auth.require', None)
    if condition is not None:
        try:
            # Try to get the current session
            cherrypy.session[SESSION_KEY]
            cherrypy.session.regenerate()
            cherrypy.request.login = cherrypy.session[SESSION_KEY]
            authenticated = True
        # If there is no session yet, try to authenticate using Basic approach
        # Note this will only work for Basic Auth without ":" character in passw
        except KeyError:
            # Get the Basic Auth header
            authheader = cherrypy.request.headers.get('AUTHORIZATION')
            if authheader:

                b64data = re.sub('Basic ', '', authheader)
                decodeddata = base64.b64decode(b64data.encode('ASCII'))
                email, passphrase = decodeddata.decode().split(":", 1)

                if user_verify(email, passphrase):
                    cherrypy.session.regenerate()
                    # Set Session value and request login, not really sure if this is needed
                    cherrypy.session[SESSION_KEY] = cherrypy.request.login = email
                    authenticated = True
                else:
                    print('Attempted to log in with HTTBA username {} but failed.'.format(email))
            else:
                print('Auth header was not present.')

        except:
            print('Ops, looks like no Authorization header was provided, mostly because other auth mechanism was used '
                  'instead of Basic')

        if not authenticated:
            raise cherrypy.HTTPError("401 Unauthorized")

        # if authenticated:
        #     for condition in conditions:
        #         if not condition():
        #             print("Authentication succeeded but authorization failed.")
        #             raise cherrypy.HTTPError("403 Forbidden")
        # else:
        #     raise cherrypy.HTTPError("401 Unauthorized")

# Let's
cherrypy.tools.crunch = cherrypy.Tool('before_handler', protect)


# def require(*conditions):
#     """A decorator that appends conditions to the auth.require config
#     variable."""
#     def decorate(f):
#         import ipdb; ipdb.set_trace()
#         if not hasattr(f, '_cp_config'):
#             f._cp_config = dict()
#         if 'auth.require' not in f._cp_config:
#             f._cp_config['auth.require'] = []
#         f._cp_config['auth.require'].extend(conditions)
#         return f
#     return decorate

#### CONDITIONS
#
# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current user as cherrypy.request.login

# # TODO: test this function with cookies, I want to make sure that cherrypy.request.login is
# #       set properly so that this function can use it.
# def user_is(reqd_email):
#     import ipdb; ipdb.set_trace()
#     return lambda: reqd_email == cherrypy.request.login

#### END CONDITIONS

def logout():
    email = cherrypy.session.get(SESSION_KEY, None)
    cherrypy.session[SESSION_KEY] = cherrypy.request.login = None
    return "Logout successful"


class Root(object):

    def __init__(self, db_settings):
        self.db = connect(db_settings)

    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True, 'tools.crunch.on': False})
    def index(self):
        import ipdb; ipdb.set_trace()
        # If authenticated, return to users view
        if SESSION_KEY in cherrypy.session:
            return cherrypy.HTTPRedirect("/users", status=301)
        else:
            return 'Welcome to Crunch.  Please <a href="/login">login</a>.'


    @cherrypy.tools.allow(methods=['GET', 'POST'])
    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True})
    # @require
    def users(self):
        """
        for GET: update this to return a json stream defining a listing of the users
        for POST: should add a new user to the users collection, with validation

        Only logged-in users should be able to connect.  If not logged in, should return the
        appropriate HTTP response.  Password information should not be revealed.

        note: Always return the appropriate response for the action requested.
        """
        import ipdb; ipdb.set_trace()
        if cherrypy.request.method is 'GET':
            return json.dumps({'users': [u for u in self.db.users.find()]})
        elif cherrypy.request.method is 'POST':
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
                password = kwargs['username']
            # Check provided password is valid
            users = self.db.users
            user = users.find_one({"email": user})
            # Check if provided password matches
            password == hashlib.sha1(user.password.encode()).hexdigest()
            if password:
                cherrypy.session[SESSION_KEY] = user.email
            return cherrypy.HTTPRedirect('/users')

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

#
# def run():
#     #settings.update(json.load(open(sys.argv[1])))
#     cherrypy.quickstart(Root(settings))

if __name__ == '__main__':
    # conf = {
    #    '/': {
    #     'tools.sessions.on': True,
    #     'tools.sessions.name': 'zknsrv',
    #     'tools.auth_basic.on': True,
    #     'tools.auth_basic.realm': 'zknsrv',
    #     'tools.auth_basic.checkpassword': validate_password,
    #     }
    # }
    config_root = {
    '/' : {
        'tools.crunch.on': True,
        'tools.sessions.on': True,
        'tools.sessions.name': 'crunch',
        }
    }
    settings.update(json.load(open(sys.argv[1])))
    main = Root(settings)
    cherrypy.quickstart(main, '/', config=config_root)