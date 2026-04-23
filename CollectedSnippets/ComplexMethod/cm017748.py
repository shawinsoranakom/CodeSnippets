def __init__(self, scope, body_file):
        self.scope = scope
        self._post_parse_error = False
        self._read_started = False
        self.resolver_match = None
        self.path = scope["path"]
        self.script_name = get_script_prefix(scope)
        if self.script_name:
            script_name = self.script_name.rstrip("/")
            if self.path.startswith(script_name + "/") or self.path == script_name:
                self.path_info = self.path[len(script_name) :]
            else:
                self.path_info = self.path
        else:
            self.path_info = self.path
        # HTTP basics.
        self.method = self.scope["method"].upper()
        # Ensure query string is encoded correctly.
        query_string = self.scope.get("query_string", "")
        if isinstance(query_string, bytes):
            query_string = query_string.decode()
        self.META = {
            "REQUEST_METHOD": self.method,
            "QUERY_STRING": query_string,
            "SCRIPT_NAME": self.script_name,
            "PATH_INFO": self.path_info,
            # WSGI-expecting code will need these for a while
            "wsgi.multithread": True,
            "wsgi.multiprocess": True,
        }
        if self.scope.get("client"):
            self.META["REMOTE_ADDR"] = self.scope["client"][0]
            self.META["REMOTE_HOST"] = self.META["REMOTE_ADDR"]
            self.META["REMOTE_PORT"] = self.scope["client"][1]
        if self.scope.get("server"):
            self.META["SERVER_NAME"] = self.scope["server"][0]
            self.META["SERVER_PORT"] = str(self.scope["server"][1])
        else:
            self.META["SERVER_NAME"] = "unknown"
            self.META["SERVER_PORT"] = "0"
        # Headers go into META.
        _headers = defaultdict(list)
        for name, value in self.scope.get("headers", []):
            name = name.decode("latin1")
            # Prevent spoofing via ambiguity between underscores and hyphens.
            if "_" in name:
                continue
            if name == "content-length":
                corrected_name = "CONTENT_LENGTH"
            elif name == "content-type":
                corrected_name = "CONTENT_TYPE"
            else:
                corrected_name = "HTTP_%s" % name.upper().replace("-", "_")
            # HTTP/2 say only ASCII chars are allowed in headers, but decode
            # latin1 just in case.
            value = value.decode("latin1")
            if corrected_name == "HTTP_COOKIE":
                value = value.rstrip("; ")
            _headers[corrected_name].append(value)
        if cookie_header := _headers.pop("HTTP_COOKIE", None):
            self.META["HTTP_COOKIE"] = "; ".join(cookie_header)
        self.META.update({name: ",".join(value) for name, value in _headers.items()})
        # Pull out request encoding, if provided.
        self._set_content_type_params(self.META)
        # Directly assign the body file to be our stream.
        self._stream = body_file
        # Other bits.
        self.resolver_match = None