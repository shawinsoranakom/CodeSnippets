def http_request(self, req):
        url = req.get_full_url()
        # resolve embedded . and ..
        url_fixed = self._fix_path(url)
        # According to RFC 3986, URLs can not contain non-ASCII characters; however this is not
        # always respected by websites: some tend to give out URLs with non percent-encoded
        # non-ASCII characters (see telemb.py, ard.py [#3412])
        # urllib chokes on URLs with non-ASCII characters (see http://bugs.python.org/issue3991)
        # To work around aforementioned issue we will replace request's original URL with
        # percent-encoded one
        # Since redirects are also affected (e.g. http://www.southpark.de/alle-episoden/s18e09)
        # the code of this workaround has been moved here from YoutubeDL.urlopen()
        url_escaped = escape_url(url_fixed)

        # Substitute URL if any change after escaping
        if url != url_escaped:
            req = update_Request(req, url=url_escaped)

        for h, v in std_headers.items():
            # Capitalize is needed because of Python bug 2275: http://bugs.python.org/issue2275
            # The dict keys are capitalized because of this bug by urllib
            if h.capitalize() not in req.headers:
                req.add_header(h, v)

        # Similarly, 'Accept-encoding'
        if 'Accept-encoding' not in req.headers:
            req.add_header(
                'Accept-Encoding', join_nonempty(
                    'gzip', 'deflate', brotli and 'br', ncompress and 'compress',
                    delim=', '))

        req.headers = handle_youtubedl_headers(req.headers)

        if sys.version_info < (2, 7):
            # avoid possible race where __r_type may be unset
            req.get_type()
            if '#' in req.get_full_url():
                # Python 2.6 is brain-dead when it comes to fragments
                req._Request__original = req._Request__original.partition('#')[0]
                req._Request__r_type = req._Request__r_type.partition('#')[0]

        # Use the totally undocumented AbstractHTTPHandler per
        # https://github.com/yt-dlp/yt-dlp/pull/4158
        return compat_urllib_request.AbstractHTTPHandler.do_request_(self, req)