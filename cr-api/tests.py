# -*- coding: utf-8 -*-
try:
    from StringIO import StringIO
    from BytesIO import BytesIO
except ImportError:
    from io import StringIO
    from io import BytesIO
import unittest
import urllib

import cherrypy

from cr.api.server import Root
from cr.db.store import global_settings as settings
from cr.db.store import Settings
from cr.db.loader import load_data

local = cherrypy.lib.httputil.Host('127.0.0.1', 50000, "")
remote = cherrypy.lib.httputil.Host('127.0.0.1', 50001, "")

DB_URL = 'mongodb://localhost:27017/test_crunchdb'


def create_db():
    settings = Settings()
    settings.url = DB_URL
    load_data(settings, True)


def setUpModule():
    cherrypy.config.update({'environment': "test_suite",
                            'tools.sessions.on': True,
                            'tools.sessions.name': 'crunch'})
    db = {
        "url": DB_URL
    }
    # prevent the HTTP server from ever starting
    cherrypy.server.unsubscribe()
    settings.update(db)
    main = Root(settings)
    create_db()
    cherrypy.tree.mount(main, '/')
    cherrypy.engine.start()
setup_module = setUpModule


def tearDownModule():
    cherrypy.engine.exit()
teardown_module = tearDownModule


class BaseCherryPyTestCase(unittest.TestCase):
    def request(self, path='/', method='GET', app_path='', scheme='http',
                proto='HTTP/1.1', data=None, headers=None, **kwargs):
        """
        CherryPy does not have a facility for serverless unit testing.
        However this recipe demonstrates a way of doing it by
        calling its internal API to simulate an incoming request.
        This will exercise the whole stack from there.

        Remember a couple of things:

        * CherryPy is multithreaded. The response you will get
          from this method is a thread-data object attached to
          the current thread. Unless you use many threads from
          within a unit test, you can mostly forget
          about the thread data aspect of the response.

        * Responses are dispatched to a mounted application's
          page handler, if found. This is the reason why you
          must indicate which app you are targetting with
          this request by specifying its mount point.

        You can simulate various request settings by setting
        the `headers` parameter to a dictionary of headers,
        the request's `scheme` or `protocol`.

        .. seealso: http://docs.cherrypy.org/stable/refman/_cprequest.html#cherrypy._cprequest.Response
        """
        # This is a required header when running HTTP/1.1
        h = {'Host': '127.0.0.1'}

        if headers is not None:
            h.update(headers)

        # If we have a POST/PUT request but no data
        # we urlencode the named arguments in **kwargs
        # and set the content-type header
        if method in ('POST', 'PUT') and not data:
            data = urllib.parse.urlencode(kwargs)
            kwargs = None
            h['content-type'] = 'application/x-www-form-urlencoded'

        # If we did have named arguments, let's
        # urlencode them and use them as a querystring
        qs = None
        if kwargs:
            qs = urllib.parse.urlencode(kwargs)

        # if we had some data passed as the request entity
        # let's make sure we have the content-length set
        fd = None
        if data is not None:
            h['content-length'] = '%d' % len(data)
            # fd = StringIO(data)
            # Python 3
            fd = BytesIO(data.encode())

        # Get our application and run the request against it
        app = cherrypy.tree.apps.get(app_path)
        if not app:
            # XXX: perhaps not the best exception to raise?
            raise AssertionError("No application mounted at '%s'" % app_path)

        # Cleanup any previous returned response
        # between calls to this method
        app.release_serving()

        # Let's fake the local and remote addresses
        request, response = app.get_serving(local, remote, scheme, proto)
        try:
            h = [(k, v) for k, v in h.items()]
            response = request.run(method, path, qs, proto, h, fd)
        finally:
            if fd:
                fd.close()
                fd = None

        if response.output_status.startswith(b'500'):
            import ipdb; ipdb.set_trace()
            print(response.body)
            raise AssertionError("Unexpected error")

        # collapse the response into a bytestring
        response.collapse_body()
        return response


class TestCherryPyCrunchApp(BaseCherryPyTestCase):

    def test_index(self):
        response = self.request('/')
        import ipdb; ipdb.set_trace()
        self.assertEqual(response.status, '200 OK')
        # Why the heck body comes as bytes?
        self.assertIn(response.body[0].decode('utf-8'), 'Welcome to Crunch.  Please <a href="/login">login</a>.')
        # Try to authenticate now
        data = {
            'username': 'admin@crunch.io',
            'password': '123456',
        }
        # Login and make sure we're redirected to users
        response = self.request('login', method='POST', **data)
        self.assertEqual(response.status, '301 Moved Permanently')

if __name__ == '__main__':
    unittest.main()