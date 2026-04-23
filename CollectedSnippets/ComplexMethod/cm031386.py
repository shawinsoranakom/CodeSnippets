def _tunnel(self):
        if _contains_disallowed_url_pchar_re.search(self._tunnel_host):
            raise ValueError('Tunnel host can\'t contain control characters %r'
                             % (self._tunnel_host,))
        connect = b"CONNECT %s:%d %s\r\n" % (
            self._wrap_ipv6(self._tunnel_host.encode("idna")),
            self._tunnel_port,
            self._http_vsn_str.encode("ascii"))
        headers = [connect]
        for header, value in self._tunnel_headers.items():
            header_bytes = header.encode("latin-1")
            value_bytes = value.encode("latin-1")
            if not _is_legal_header_name(header_bytes):
                raise ValueError('Invalid header name %r' % (header_bytes,))
            if _is_illegal_header_value(value_bytes):
                raise ValueError('Invalid header value %r' % (value_bytes,))
            headers.append(b"%s: %s\r\n" % (header_bytes, value_bytes))
        headers.append(b"\r\n")
        # Making a single send() call instead of one per line encourages
        # the host OS to use a more optimal packet size instead of
        # potentially emitting a series of small packets.
        self.send(b"".join(headers))
        del headers

        response = self.response_class(self.sock, method=self._method)
        try:
            (version, code, message) = response._read_status()

            self._raw_proxy_headers = _read_headers(response.fp, self.max_response_headers)

            if self.debuglevel > 0:
                for header in self._raw_proxy_headers:
                    print('header:', header.decode())

            if code != http.HTTPStatus.OK:
                self.close()
                raise OSError(f"Tunnel connection failed: {code} {message.strip()}")

        finally:
            response.close()