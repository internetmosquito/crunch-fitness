import cherrypy
import hashlib
import json
import sys
from bson import json_util
import itertools
import math
import numpy as np

from cr.db.store import global_settings as settings
from cr.db.store import connect


SESSION_KEY = 'user'
main = None

# A formatting helper
float_formatter = lambda x: "%.2f" % x


def get_np_array_from_users(users):
    """
    A naive way to transform the collection of users to a numpy array, suboptimal and might require
    to find a decent driver to do this, but for testing is ok for now
    :param users: The list containing our users collection
    :return: A numpy array containing tuples (lat, lng) or None if there were no users
    """
    np_array = None
    if users:
        points = [(user['latitude'], user['longitude']) for user in users]
        dt = np.dtype('float, float')
        np_array = np.array(points, dtype=dt)
        return np_array
    return np_array


def get_metrics_for_distances(distances):
    """
    Given an array with distances, will return max, min and average and std in meters
    :param distances: A list where each element is a float representing a distance in meters
    :return: Maximun, Minimun and average distances
    """
    max_d = min_d = avg_d = std_d = 0.0
    if distances:
        # Reconstruct an numpy array from distances
        np_array = np.array(distances)
        max_d = float_formatter(np.amax(np_array))
        min_d = float_formatter(np.amin(np_array))
        avg_d = float_formatter(np.average(np_array))
        std_d = float_formatter(np.std(np_array))

    return max_d, min_d, avg_d, std_d


def np_haversine(point_a, point_b):
    """
    Calculates great circle distance using Haversine formula
    :param point_a: The first pair lat-lng
    :param point_b: The second pair lat-lng
    :return: The calculated distance, in kilometers
    """
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [point_a[0],
                                                point_a[1],
                                                point_b[0],
                                                point_b[1]])
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1
    # This is the Haversine function https://en.wikipedia.org/wiki/Haversine_formula,
    # Used to calculate great circle distance, assuming earth is a perfect Sphere
    # But using Numpy functions instead
    a = np.sin(d_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(d_lon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    # Radius of earth in in km is 6371
    r = 6371
    return c*r


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
            raise cherrypy.HTTPError(401, u'Not authorized to access this resource. Please login.')

# Specify the hook
cherrypy.tools.crunch = cherrypy.Tool('before_handler', protect)


class Root(object):

    def __init__(self, db_settings):
        self.db = connect(db_settings)

    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True, 'tools.crunch.on': False})
    def index(self):
        # If authenticated, return to users view
        if SESSION_KEY in cherrypy.session:
                raise cherrypy.HTTPRedirect(u'/users', status=301)
        else:
            return 'Welcome to Crunch.  Please <a href="/login">login</a>.'


    @cherrypy.tools.allow(methods=['GET', 'POST'])
    @cherrypy.expose
    @cherrypy.config(**{'auth.require': True})
    @cherrypy.tools.json_in()
    def users(self, *args, **kwargs):
        """
        for GET: update this to return a json stream defining a listing of the users
        for POST: should add a new user to the users collection, with validation

        Only logged-in users should be able to connect.  If not logged in, should return the
        appropriate HTTP response.  Password information should not be revealed.

        note: Always return the appropriate response for the action requested.
        """
        if cherrypy.request.method == 'GET':
            return json.dumps({'users': [u for u in self.db.users.find()]}, default=json_util.default)
        elif cherrypy.request.method == 'POST':
            # Get post form data and create a new user
            input_json = cherrypy.request.json
            new_id = self.db.users.insert_one(input_json)
            new_user = self.db.users.find_one(new_id.inserted_id)
            cherrypy.response.status = 201
            return json.dumps(new_user, default=json_util.default)


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
                if self.user_verify(user, password):
                    # FIXME: Not sure if this is needed, in theory Cherrypy recreates session if cookie ID != session ID
                    cherrypy.session.regenerate()
                    cherrypy.session[SESSION_KEY] = cherrypy.request.login = user
                    # Redirect to users
                    raise cherrypy.HTTPRedirect(u'/users', status=301)
                else:
                    raise cherrypy.HTTPError(u'401 Unauthorized')
            else:
                raise cherrypy.HTTPError(u'401 Please provide username and password')


    @cherrypy.tools.allow(methods=['GET'])
    @cherrypy.expose
    def logout(self):
        """
        Should log the user out, rendering them incapable of accessing the users endpoint, but
        """
        if SESSION_KEY in cherrypy.session:
            cherrypy.session.regenerate()
            return 'Logged out, we will miss you dearly!.'
        else:
            raise cherrypy.HTTPRedirect(u'/', status=301)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET', 'POST'])
    @cherrypy.config(**{'auth.require': True})
    @cherrypy.tools.json_out()
    def distances(self):
        """
        Each user has a lat/lon associated with them.  Using only numpy, determine the distance
        between each user pair, and provide the min/max/average/std as a json response.
        This should be GET only.

        Don't code, but explain how would you scale this to 1,000,000 users, considering users
        changing position every few minutes?
        """
        users = self.db.users.find()
        np_array = get_np_array_from_users(users)
        distances = []
        # FIXME: this approach takes O(n*n) complexity, not the best approach, will be quadratic in no time
        for point_a, point_b in itertools.combinations(np_array, 2):
            distances.append(np_haversine(point_a, point_b))

        max_d, min_d, avg_d, std_d = get_metrics_for_distances(distances)
        response = {}
        response['Maximun distance'] = max_d
        response['Minimum distance'] = min_d
        response['Average distance'] = avg_d
        response['Standard deviation'] = std_d
        return response

    def user_verify(self, username, password):
        """
        Simply checks if a user with provided email and pass exists in db
        :param username: User email
        :param password:  User pass
        :return: True if user found
        """
        users = self.db.users
        user = users.find_one({"email": username})
        if user:
            password = hashlib.sha1(password.encode()).hexdigest()
            return password == user['hash']
        return False

if __name__ == '__main__':
    config_root = {'/': {
        'tools.crunch.on': True,
        'tools.sessions.on': True,
        'tools.sessions.name': 'crunch', }
    }
    settings.update(json.load(open(sys.argv[1])))
    main = Root(settings)
    cherrypy.quickstart(main, '/', config=config_root)