def open(self, method, url, data=None, headers=None, use_proxy=None,
             force=None, last_mod_time=None, timeout=None, validate_certs=None,
             url_username=None, url_password=None, http_agent=None,
             force_basic_auth=None, follow_redirects=None,
             client_cert=None, client_key=None, cookies=None, use_gssapi=False,
             unix_socket=None, ca_path=None, unredirected_headers=None, decompress=None,
             ciphers=None, use_netrc=None, context=None):
        """
        Sends a request via HTTP(S) or FTP using urllib (Python3)

        Does not require the module environment

        Returns :class:`HTTPResponse` object.

        :arg method: method for the request
        :arg url: URL to request

        :kwarg data: (optional) bytes, or file-like object to send
            in the body of the request
        :kwarg headers: (optional) Dictionary of HTTP Headers to send with the
            request
        :kwarg use_proxy: (optional) Boolean of whether or not to use proxy
        :kwarg force: (optional) Boolean of whether or not to set `cache-control: no-cache` header
        :kwarg last_mod_time: (optional) Datetime object to use when setting If-Modified-Since header
        :kwarg timeout: (optional) How long to wait for the server to send
            data before giving up, as a float
        :kwarg validate_certs: (optional) Booleani that controls whether we verify
            the server's TLS certificate
        :kwarg url_username: (optional) String of the user to use when authenticating
        :kwarg url_password: (optional) String of the password to use when authenticating
        :kwarg http_agent: (optional) String of the User-Agent to use in the request
        :kwarg force_basic_auth: (optional) Boolean determining if auth header should be sent in the initial request
        :kwarg follow_redirects: (optional) String of urllib2, all, safe, none to determine how redirects are
            followed, see HTTPRedirectHandler for more information
        :kwarg client_cert: (optional) PEM formatted certificate chain file to be used for SSL client authentication.
            This file can also include the key as well, and if the key is included, client_key is not required
        :kwarg client_key: (optional) PEM formatted file that contains your private key to be used for SSL client
            authentication. If client_cert contains both the certificate and key, this option is not required
        :kwarg cookies: (optional) CookieJar object to send with the
            request
        :kwarg use_gssapi: (optional) Use GSSAPI handler of requests.
        :kwarg unix_socket: (optional) String of file system path to unix socket file to use when establishing
            connection to the provided url
        :kwarg ca_path: (optional) String of file system path to CA cert bundle to use
        :kwarg unredirected_headers: (optional) A list of headers to not attach on a redirected request
        :kwarg decompress: (optional) Whether to attempt to decompress gzip content-encoded responses
        :kwarg ciphers: (optional) List of ciphers to use
        :kwarg use_netrc: (optional) Boolean determining whether to use credentials from ~/.netrc file
        :kwarg context: (optional) ssl.Context object for SSL validation. When provided, all other SSL related
            arguments are ignored. See make_context.
        :returns: HTTPResponse. Added in Ansible 2.9
        """

        if headers is None:
            headers = {}
        elif not isinstance(headers, dict):
            raise ValueError("headers must be a dict")
        headers = dict(self.headers, **headers)

        use_proxy = self._fallback(use_proxy, self.use_proxy)
        force = self._fallback(force, self.force)
        timeout = self._fallback(timeout, self.timeout)
        validate_certs = self._fallback(validate_certs, self.validate_certs)
        url_username = self._fallback(url_username, self.url_username)
        url_password = self._fallback(url_password, self.url_password)
        http_agent = self._fallback(http_agent, self.http_agent)
        force_basic_auth = self._fallback(force_basic_auth, self.force_basic_auth)
        follow_redirects = self._fallback(follow_redirects, self.follow_redirects)
        client_cert = self._fallback(client_cert, self.client_cert)
        client_key = self._fallback(client_key, self.client_key)
        cookies = self._fallback(cookies, self.cookies)
        unix_socket = self._fallback(unix_socket, self.unix_socket)
        ca_path = self._fallback(ca_path, self.ca_path)
        unredirected_headers = self._fallback(unredirected_headers, self.unredirected_headers)
        decompress = self._fallback(decompress, self.decompress)
        ciphers = self._fallback(ciphers, self.ciphers)
        use_netrc = self._fallback(use_netrc, self.use_netrc)
        context = self._fallback(context, self.context)

        handlers = []

        if unix_socket:
            handlers.append(UnixHTTPHandler(unix_socket))

        url, auth_headers, auth_handlers = _configure_auth(url, url_username, url_password, use_gssapi, force_basic_auth, use_netrc)
        headers.update(auth_headers)
        handlers.extend(auth_handlers)

        if not use_proxy:
            proxyhandler = urllib.request.ProxyHandler({})
            handlers.append(proxyhandler)

        if not context:
            context = make_context(
                cafile=ca_path,
                ciphers=ciphers,
                validate_certs=validate_certs,
                client_cert=client_cert,
                client_key=client_key,
            )
        if unix_socket:
            ssl_handler = UnixHTTPSHandler(unix_socket=unix_socket, context=context)
        else:
            ssl_handler = urllib.request.HTTPSHandler(context=context)
        handlers.append(ssl_handler)

        handlers.append(HTTPRedirectHandler(follow_redirects))

        # add some nicer cookie handling
        if cookies is not None:
            handlers.append(urllib.request.HTTPCookieProcessor(cookies))

        opener = urllib.request.build_opener(*handlers)
        urllib.request.install_opener(opener)

        data = to_bytes(data, nonstring='passthru')
        request = urllib.request.Request(url, data=data, method=method.upper())

        # add the custom agent header, to help prevent issues
        # with sites that block the default urllib agent string
        if http_agent:
            request.add_header('User-agent', http_agent)

        # Cache control
        # Either we directly force a cache refresh
        if force:
            request.add_header('cache-control', 'no-cache')
        # or we do it if the original is more recent than our copy
        elif last_mod_time:
            tstamp = rfc2822_date_string(last_mod_time.timetuple(), 'GMT')
            request.add_header('If-Modified-Since', tstamp)

        # user defined headers now, which may override things we've set above
        unredirected_headers = [h.lower() for h in (unredirected_headers or [])]
        for header in headers:
            if header.lower() in unredirected_headers:
                request.add_unredirected_header(header, headers[header])
            else:
                request.add_header(header, headers[header])

        r = urllib.request.urlopen(request, None, timeout)
        if decompress and r.headers.get('content-encoding', '').lower() == 'gzip':
            fp = GzipDecodedReader(r.fp)
            r.fp = fp
            # Content-Length does not match gzip decoded length
            # Prevent ``r.read`` from stopping at Content-Length
            r.length = None
        return r