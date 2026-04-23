def load(self, filename=None, ignore_discard=True, ignore_expires=True):
        """Load cookies from a file."""
        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                raise ValueError(http.cookiejar.MISSING_FILENAME_TEXT)

        def prepare_line(line):
            if line.startswith(self._HTTPONLY_PREFIX):
                line = line[len(self._HTTPONLY_PREFIX):]
            # comments and empty lines are fine
            if line.startswith('#') or not line.strip():
                return line
            cookie_list = line.split('\t')
            if len(cookie_list) != self._ENTRY_LEN:
                raise http.cookiejar.LoadError(f'invalid length {len(cookie_list)}')
            cookie = self._CookieFileEntry(*cookie_list)
            if cookie.expires_at and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', cookie.expires_at):
                raise http.cookiejar.LoadError(f'invalid expires at {cookie.expires_at}')
            return line

        cf = io.StringIO()
        with self.open(filename) as f:
            for line in f:
                try:
                    cf.write(prepare_line(line))
                except http.cookiejar.LoadError as e:
                    if f'{line.strip()} '[0] in '[{"':
                        raise http.cookiejar.LoadError(
                            'Cookies file must be Netscape formatted, not JSON. See  '
                            'https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp')
                    write_string(f'WARNING: skipping cookie file entry due to {e}: {line!r}\n')
                    continue
        cf.seek(0)
        self._really_load(cf, filename, ignore_discard, ignore_expires)
        # Session cookies are denoted by either `expires` field set to
        # an empty string or 0. MozillaCookieJar only recognizes the former
        # (see [1]). So we need force the latter to be recognized as session
        # cookies on our own.
        # Session cookies may be important for cookies-based authentication,
        # e.g. usually, when user does not check 'Remember me' check box while
        # logging in on a site, some important cookies are stored as session
        # cookies so that not recognizing them will result in failed login.
        # 1. https://bugs.python.org/issue17164
        for cookie in self:
            # Treat `expires=0` cookies as session cookies
            if cookie.expires == 0:
                cookie.expires = None
                cookie.discard = True