**SOME NOTES**

Need to run createdb first in order to populate database with some data, is just a thin wrapper on load_data from cr.db
module. You can use that directly but this will avoid having to import and use that package.

Keep in mind we're using Python 3 for this.

In order to start the server, simply:

```
python server.py settings.json
```

The JSON file contains simply the db URL that is required by the Settings object from cr.db package.

Testing some stuff with CURL:

You can use the browser but is always more fun with Curl :)

Let's make a request to login to authenticate.

```
curl --cookie-jar cookie.jar --data "username=some@user.com&password=somesecret" http://localhost:8080/login
```

You can inspect the generated cookie.jar file, then let's make a call to users endpoint

```
curl --cookie "crunch=d1faadf80031fd8c91a45c7c2f5cf32f4f518e40" http://localhost:8080/login
```

Login out, simply call

```
curl --cookie "crunch=d1faadf80031fd8c91a45c7c2f5cf32f4f518e40" http://localhost:8080/logout
```

**TESTING**

Still work in progress, had to mock some session object because for some reason while testing session data is removed 
between requests.

To run cr.api tests:

```
cd cr/api
py.test -s tests.py
```

