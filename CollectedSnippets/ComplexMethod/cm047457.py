def wsgi_environ(self):
        environ = {
            key: val for key, val in request.httprequest.environ.items()
            if (key.startswith('HTTP_')  # headers
             or key.startswith('REMOTE_')
             or key.startswith('REQUEST_')
             or key.startswith('SERVER_')
             or key.startswith('werkzeug.proxy_fix.')
             or key in WSGI_SAFE_KEYS)
        }

        return request.make_response(
            json.dumps(environ, indent=4),
            headers=list(CT_JSON.items())
        )