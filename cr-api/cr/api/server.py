import cherrypy
import json
import sys
from cr.db.store import global_settings as settings, connect


class Root(object):

    def __init__(self, settings):
        self.db = connect(settings)

    def index(self):
        return 'Welcome to Crunch.  Please <a href="/login">login</a>.'
    index.exposed = True

    def users(self):
        """
        for GET: update this to return a json stream defining a listing of the users
        for POST: should add a new user to the users collection, with validation

        Only logged-in users should be able to connect.  If not logged in, should return the
        appropriate HTTP response.  Password information should not be revealed.

        note: Always return the appropriate response for the action requested.
        """
        return json.dumps({'users': [u for u in self.db.users.find()]})

    users.exposed = True

    def login(self):
        """
        a GET to this endpoint should provide the user login/logout capabilities

        a POST to this endpoint with credentials should set up persistence tokens for the user,
        allowing them to access other pages.

        hint: this is how the admin's password was generated:
              import hashlib; hashlib.sha1('123456').hexdigest()
        """

    def logout(self):
        """
        Should log the user out, rendering them incapable of accessing the users endpoint, but
        """

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
    import ipdb; ipdb.set_trace()
    settings.update(json.load(open(sys.argv[1])))
    cherrypy.quickstart(Root(settings))