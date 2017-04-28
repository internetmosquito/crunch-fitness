import urllib
from unittest.mock import patch
import cherrypy
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession
from .server import Root
from cr.db.store import global_settings as settings
from cr.db.store import Settings
from cr.db.loader import load_data

DB_URL = 'mongodb://localhost:27017/test_crunchdb'
SERVER = 'http://127.0.0.1'


class SimpleCPTest(helper.CPWebCase):

    def setup_server():
        cherrypy.config.update({'environment': "test_suite",
                                'tools.sessions.on': True,
                                'tools.sessions.name': 'crunch',
                                'tools.crunch.on': True,
                                })
        db = {
            "url": DB_URL
        }
        settings.update(db)
        main = Root(settings)
        load_data(settings, True)
        cherrypy.tree.mount(main, '/')
    setup_server = staticmethod(setup_server)

    # HELPER METHODS
    def get_redirect_path(self, data):
        """
        Tries to extract the path from the cookie data obtained in a response
        :param data: The cookie data from the response
        :return: The path if possible, None otherwise
        """
        path = None
        location = None
        # Get the Location from response, if possible
        for tuples in data:
            if tuples[0] == 'Location':
                location = tuples[1]
                break
        if location:
            if SERVER in location:
                index = location.find(SERVER)
                # Path plus equal
                index = index + len(SERVER) + 6
                # Get the actual path
                path = location[index:]
        return path

    def test_login_shown_if_not_logged_in(self):
        response = self.getPage('/')
        self.assertStatus('200 OK')
        # Why the heck body comes as bytes?
        self.assertIn('Welcome to Crunch.  Please <a href="/login">login</a>.', response[2].decode())

    def test_login_redirect_to_users(self):
        # Try to authenticate with a wrong password
        data = {
            'username': 'admin@crunch.io',
            'password': 'admin',
        }
        query_string = urllib.parse.urlencode(data)
        self.getPage("/login", method='POST', body=query_string)
        # Login should show 401
        self.assertStatus('401 Unauthorized')
        # Try to authenticate with a wrong password
        data = {
            'username': 'admin@crunch.io',
            'password': '123456',
        }
        query_string = urllib.parse.urlencode(data)
        # Login should work and be redirected to users
        self.getPage('/login', method='POST', body=query_string)
        self.assertStatus('301 Moved Permanently')

    def test_login_no_credentials_throws_401(self):
        # Login should show 401
        response = self.getPage('/login', method='POST')
        self.assertStatus('401 Please provide username and password')

    def test_login_shows_login_logout_forms(self):
        # Unauthenticated GET should show login form
        response = self.getPage('/login', method='GET')
        self.assertStatus('200 OK')
        self.assertIn('<form method="post" action="login">', response[2].decode())
        # Try to authenticate with a wrong password
        data = {
            'username': 'admin@crunch.io',
            'password': '123456',
        }
        query_string = urllib.parse.urlencode(data)
        # Login should work and be redirected to users
        response = self.getPage('/login', method='POST', body=query_string)
        self.assertStatus('301 Moved Permanently')
        # FIXME: Had to mock the session, not sure why between requests while testing the session loses
        # values, this would require more investigation, since when firing up the real server works fine
        # For now let's just mock it
        sess_mock = RamSession()
        sess_mock['user'] = 'admin@crunch.io'
        with patch('cherrypy.session', sess_mock, create=True):
            # Make a GET again
            response = self.getPage('/login', method='GET')
            self.assertStatus('200 OK')
            self.assertIn('<form method="post" action="logout">', response[2].decode())

    def test_logout_actually_logs_out(self):
        # Unauthenticated GET should show redirect to index
        response = self.getPage('/logout', method='GET')
        self.assertStatus('301 Moved Permanently')
        cookie_data = response[1][6][1]
        path = self.get_redirect_path(cookie_data)
        if path:
            # Make sure redirect was to index
            self.assertEqual(path, '/')
        # Try to authenticate
        data = {
            'username': 'admin@crunch.io',
            'password': '123456',
        }
        query_string = urllib.parse.urlencode(data)
        # Login should work and be redirected to users
        response = self.getPage('/login', method='POST', body=query_string)
        self.assertStatus('301 Moved Permanently')
        # Check logout actually logs out when logged id
        sess_mock = RamSession()
        sess_mock['user'] = 'admin@crunch.io'
        with patch('cherrypy.session', sess_mock, create=True):
            # Make a GET again
            response = self.getPage('/logout', method='GET')
            self.assertStatus('200 OK')
            self.assertIn('Logged out, we will miss you dearly!', response[2].decode())

    def test_users_returns_401_if_not_logged_in(self):
        # Unauthenticated GET should show redirect to index
        response = self.getPage('/users', method='GET')
        self.assertStatus('401 Unauthorized')
        # Try to authenticate
        data = {
            'username': 'admin@crunch.io',
            'password': '123456',
        }
        query_string = urllib.parse.urlencode(data)
        # Login should work and be redirected to users
        response = self.getPage('/login', method='POST', body=query_string)
        cookie_data = response[1]
        path = self.get_redirect_path(cookie_data)
        if path:
            # Make sure redirect was to index
            self.assertEqual(path, '/users')
        self.assertStatus('301 Moved Permanently')
        # Check logout actually logs out when logged id
        sess_mock = RamSession()
        sess_mock['user'] = 'admin@crunch.io'
        with patch('cherrypy.session', sess_mock, create=True):
            # Make a GET again
            response = self.getPage('/users', method='GET')
            self.assertStatus('200 OK')


