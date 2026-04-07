def _base_environ(self, **request):
        """
        The base environment for a request.
        """
        # This is a minimal valid WSGI environ dictionary, plus:
        # - HTTP_COOKIE: for cookie support,
        # - REMOTE_ADDR: often useful, see #8551.
        # See https://www.python.org/dev/peps/pep-3333/#environ-variables
        return {
            "HTTP_COOKIE": "; ".join(
                sorted(
                    "%s=%s" % (morsel.key, morsel.coded_value)
                    for morsel in self.cookies.values()
                )
            ),
            "PATH_INFO": "/",
            "REMOTE_ADDR": "127.0.0.1",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "",
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": FakePayload(b""),
            "wsgi.errors": self.errors,
            "wsgi.multiprocess": True,
            "wsgi.multithread": False,
            "wsgi.run_once": False,
            **self.defaults,
            **request,
        }