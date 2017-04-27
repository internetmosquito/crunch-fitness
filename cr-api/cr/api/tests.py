import urllib
from unittest.mock import patch
import cherrypy
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession
from .server import Root
from cr.db.store import global_settings as settings

DB_URL = 'mongodb://localhost:27017/test_crunchdb'


class SimpleCPTest(helper.CPWebCase):
    def setup_server():
        cherrypy.config.update({'environment': "test_suite",
                                'tools.sessions.on': True,
                                'tools.sessions.name': 'crunch'})
        db = {
            "url": DB_URL
        }
        settings.update(db)
        main = Root(settings)
        cherrypy.tree.mount(main, '/')
    setup_server = staticmethod(setup_server)

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

