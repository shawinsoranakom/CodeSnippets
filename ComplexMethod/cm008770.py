def http_response(self, req, resp):
        old_resp = resp

        # Content-Encoding header lists the encodings in order that they were applied [1].
        # To decompress, we simply do the reverse.
        # [1]: https://datatracker.ietf.org/doc/html/rfc9110#name-content-encoding
        decoded_response = None
        for encoding in (e.strip() for e in reversed(resp.headers.get('Content-encoding', '').split(','))):
            if encoding == 'gzip':
                decoded_response = self.gz(decoded_response or resp.read())
            elif encoding == 'deflate':
                decoded_response = self.deflate(decoded_response or resp.read())
            elif encoding == 'br' and brotli:
                decoded_response = self.brotli(decoded_response or resp.read())

        if decoded_response is not None:
            resp = urllib.request.addinfourl(io.BytesIO(decoded_response), old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # Percent-encode redirect URL of Location HTTP header to satisfy RFC 3986 (see
        # https://github.com/ytdl-org/youtube-dl/issues/6457).
        if 300 <= resp.code < 400:
            location = resp.headers.get('Location')
            if location:
                # As of RFC 2616 default charset is iso-8859-1 that is respected by Python 3
                location = location.encode('iso-8859-1').decode()
                location_escaped = normalize_url(location)
                if location != location_escaped:
                    del resp.headers['Location']
                    resp.headers['Location'] = location_escaped
        return resp