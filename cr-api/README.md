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

Log out, simply call

```
curl --cookie "crunch=d1faadf80031fd8c91a45c7c2f5cf32f4f518e40" http://localhost:8080/logout
```

Calling users, if not logged in, will return 401

```
curl --cookie "crunch=d1faadf80031fd8c91a45c7c2f5cf32f4f518e40" http://localhost:8080/users
```

If loggged in will return the list of current users.

Creating a user with a POST request, JSON format and headers required.

```
curl --cookie "crunch=3d4ec90976b6ecce9ee0b5b8dd929f67264482a0" -H "Content-Type: application/json" -X POST -d '{"email":"john@doe.com","hash":"f9a4d6c9b146c1e4a8e9ed904e2f9da5564baed6", "last_name": "Doe", "latitude": 43.39382215044702, "longitude": -1.7757511138916016, "registered": "Thursday, July 12, 2016 3:00 AM", "first_name": "John", "company": "ACME CORP."}' http://127.0.0.1:8080/users
```

**TESTING**

Still work in progress, had to mock some session object because for some reason while testing session data is removed 
between requests.

This is a real pain because I can't truly check while testing in protected resources are really protected, although
this works fine in real mode. 

To run cr.api tests:

```
cd cr/api
py.test -s tests.py
```

**TODO**

Gotta provide password in plain text when creating users with POST instead of passing the hash directly and also check provided fields are good and all required