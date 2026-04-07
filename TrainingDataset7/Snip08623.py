def __init__(self, environ):
        script_name = get_script_name(environ)
        # If PATH_INFO is empty (e.g. accessing the SCRIPT_NAME URL without a
        # trailing slash), operate as if '/' was requested.
        path_info = get_path_info(environ) or "/"
        self.environ = environ
        self.path_info = path_info
        # be careful to only replace the first slash in the path because of
        # http://test/something and http://test//something being different as
        # stated in RFC 3986.
        self.path = "%s/%s" % (script_name.rstrip("/"), path_info.replace("/", "", 1))
        self.META = environ
        self.META["PATH_INFO"] = path_info
        self.META["SCRIPT_NAME"] = script_name
        self.method = environ["REQUEST_METHOD"].upper()
        # Set content_type, content_params, and encoding.
        self._set_content_type_params(environ)
        try:
            content_length = int(environ.get("CONTENT_LENGTH"))
        except (ValueError, TypeError):
            content_length = 0
        self._stream = LimitedStream(self.environ["wsgi.input"], content_length)
        self._read_started = False
        self.resolver_match = None