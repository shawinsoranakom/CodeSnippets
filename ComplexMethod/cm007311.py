def http_response(self, req, resp):
        old_resp = resp

        # Content-Encoding header lists the encodings in order that they were applied [1].
        # To decompress, we simply do the reverse.
        # [1]: https://datatracker.ietf.org/doc/html/rfc9110#name-content-encoding
        decoded_response = None
        decoders = {
            'gzip': self.deflate_gz,
            'deflate': self.deflate_gz,
        }
        if brotli:
            decoders['br'] = self.brotli
        if ncompress:
            decoders['compress'] = self.compress
        if sys.platform.startswith('java'):
            # Jython zlib implementation misses gzip
            decoders['gzip'] = self.gzip

        def encodings(hdrs):
            # A header field that allows multiple values can have multiple instances [2].
            # [2]: https://datatracker.ietf.org/doc/html/rfc9110#name-fields
            for e in reversed(','.join(hdrs).split(',')):
                if e:
                    yield e.strip()

        encodings_left = []
        try:
            resp.headers.get_all
            hdrs = resp.headers
        except AttributeError:
            # Py2 has no get_all() method: headers are rfc822.Message
            from email.message import Message
            hdrs = Message()
            for k, v in resp.headers.items():
                hdrs[k] = v

        decoder, decoded_response = True, None
        for encoding in encodings(hdrs.get_all('Content-Encoding', [])):
            # "SHOULD consider" x-compress, x-gzip as compress, gzip
            decoder = decoder and decoders.get(remove_start(encoding, 'x-'))
            if not decoder:
                encodings_left.insert(0, encoding)
                continue
            decoded_response = decoder(decoded_response or resp.read())
        if decoded_response is not None:
            resp = compat_urllib_request.addinfourl(
                io.BytesIO(decoded_response), old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
            del resp.headers['Content-Length']
            resp.headers['Content-Length'] = '%d' % len(decoded_response)
        del resp.headers['Content-Encoding']
        if encodings_left:
            resp.headers['Content-Encoding'] = ', '.join(encodings_left)

        # Percent-encode redirect URL of Location HTTP header to satisfy RFC 3986 (see
        # https://github.com/ytdl-org/youtube-dl/issues/6457).
        if 300 <= resp.code < 400:
            location = resp.headers.get('Location')
            if location:
                # As of RFC 2616 default charset is iso-8859-1 that is respected by python 3
                if sys.version_info >= (3, 0):
                    location = location.encode('iso-8859-1')
                location = location.decode('utf-8')
                # resolve embedded . and ..
                location_fixed = self._fix_path(location)
                location_escaped = escape_url(location_fixed)
                if location != location_escaped:
                    del resp.headers['Location']
                    if not isinstance(location_escaped, str):  # Py 2 case
                        location_escaped = location_escaped.encode('utf-8')
                    resp.headers['Location'] = location_escaped
        return resp