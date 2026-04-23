def putrequest(self, method, url, skip_host=False,
                   skip_accept_encoding=False):
        """Send a request to the server.

        'method' specifies an HTTP request method, e.g. 'GET'.
        'url' specifies the object being requested, e.g. '/index.html'.
        'skip_host' if True does not add automatically a 'Host:' header
        'skip_accept_encoding' if True does not add automatically an
           'Accept-Encoding:' header
        """

        # if a prior response has been completed, then forget about it.
        if self.__response and self.__response.isclosed():
            self.__response = None


        # in certain cases, we cannot issue another request on this connection.
        # this occurs when:
        #   1) we are in the process of sending a request.   (_CS_REQ_STARTED)
        #   2) a response to a previous request has signalled that it is going
        #      to close the connection upon completion.
        #   3) the headers for the previous response have not been read, thus
        #      we cannot determine whether point (2) is true.   (_CS_REQ_SENT)
        #
        # if there is no prior response, then we can request at will.
        #
        # if point (2) is true, then we will have passed the socket to the
        # response (effectively meaning, "there is no prior response"), and
        # will open a new one when a new request is made.
        #
        # Note: if a prior response exists, then we *can* start a new request.
        #       We are not allowed to begin fetching the response to this new
        #       request, however, until that prior response is complete.
        #
        if self.__state == _CS_IDLE:
            self.__state = _CS_REQ_STARTED
        else:
            raise CannotSendRequest(self.__state)

        self._validate_method(method)

        # Save the method for use later in the response phase
        self._method = method

        url = url or '/'
        self._validate_path(url)

        request = '%s %s %s' % (method, url, self._http_vsn_str)

        self._output(self._encode_request(request))

        if self._http_vsn == 11:
            # Issue some standard headers for better HTTP/1.1 compliance

            if not skip_host:
                # this header is issued *only* for HTTP/1.1
                # connections. more specifically, this means it is
                # only issued when the client uses the new
                # HTTPConnection() class. backwards-compat clients
                # will be using HTTP/1.0 and those clients may be
                # issuing this header themselves. we should NOT issue
                # it twice; some web servers (such as Apache) barf
                # when they see two Host: headers

                # If we need a non-standard port,include it in the
                # header.  If the request is going through a proxy,
                # but the host of the actual URL, not the host of the
                # proxy.

                netloc = ''
                if url.startswith('http'):
                    nil, netloc, nil, nil, nil = urlsplit(url)

                if netloc:
                    try:
                        netloc_enc = netloc.encode("ascii")
                    except UnicodeEncodeError:
                        netloc_enc = netloc.encode("idna")
                    self.putheader('Host', _strip_ipv6_iface(netloc_enc))
                else:
                    if self._tunnel_host:
                        host = self._tunnel_host
                        port = self._tunnel_port
                    else:
                        host = self.host
                        port = self.port

                    try:
                        host_enc = host.encode("ascii")
                    except UnicodeEncodeError:
                        host_enc = host.encode("idna")

                    # As per RFC 273, IPv6 address should be wrapped with []
                    # when used as Host header
                    host_enc = self._wrap_ipv6(host_enc)
                    if ":" in host:
                        host_enc = _strip_ipv6_iface(host_enc)

                    if port == self.default_port:
                        self.putheader('Host', host_enc)
                    else:
                        host_enc = host_enc.decode("ascii")
                        self.putheader('Host', "%s:%s" % (host_enc, port))

            # note: we are assuming that clients will not attempt to set these
            #       headers since *this* library must deal with the
            #       consequences. this also means that when the supporting
            #       libraries are updated to recognize other forms, then this
            #       code should be changed (removed or updated).

            # we only want a Content-Encoding of "identity" since we don't
            # support encodings such as x-gzip or x-deflate.
            if not skip_accept_encoding:
                self.putheader('Accept-Encoding', 'identity')

            # we can accept "chunked" Transfer-Encodings, but no others
            # NOTE: no TE header implies *only* "chunked"
            #self.putheader('TE', 'chunked')

            # if TE is supplied in the header, then it must appear in a
            # Connection header.
            #self.putheader('Connection', 'TE')

        else:
            # For HTTP/1.0, the server will assume "not chunked"
            pass