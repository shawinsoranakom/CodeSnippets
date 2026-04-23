def redirect_request(self, req, fp, code, msg, headers, newurl):
        follow_redirects = self.follow_redirects

        # Preserve urllib2 compatibility
        if follow_redirects in ('urllib2', 'urllib'):
            return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)

        # Handle disabled redirects
        elif follow_redirects in ('none', False):
            raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

        method = req.get_method()

        # Handle non-redirect HTTP status or invalid follow_redirects
        if follow_redirects in ('all', True):
            if code < 300 or code >= 400:
                raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)
        elif follow_redirects == 'safe':
            if code < 300 or code >= 400 or method not in ('GET', 'HEAD'):
                raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)
        else:
            raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        data = req.data
        origin_req_host = req.origin_req_host

        # Be conciliant with URIs containing a space
        newurl = newurl.replace(' ', '%20')

        # Support redirect with payload and original headers
        if code in (307, 308):
            # Preserve payload and headers
            req_headers = req.headers
        else:
            # Do not preserve payload and filter headers
            data = None
            req_headers = {k: v for k, v in req.headers.items()
                           if k.lower() not in ("content-length", "content-type", "transfer-encoding")}

            # http://tools.ietf.org/html/rfc7231#section-6.4.4
            if code == 303 and method != 'HEAD':
                method = 'GET'

            # Do what the browsers do, despite standards...
            # First, turn 302s into GETs.
            if code == 302 and method != 'HEAD':
                method = 'GET'

            # Second, if a POST is responded to with a 301, turn it into a GET.
            if code == 301 and method == 'POST':
                method = 'GET'

        return urllib.request.Request(
            newurl,
            data=data,
            headers=req_headers,
            origin_req_host=origin_req_host,
            unverifiable=True,
            method=method.upper(),
        )