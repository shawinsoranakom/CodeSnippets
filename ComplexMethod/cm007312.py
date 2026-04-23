def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        """
        Save cookies to a file.

        Most of the code is taken from CPython 3.8 and slightly adapted
        to support cookie files with UTF-8 in both python 2 and 3.
        """
        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                raise ValueError(compat_cookiejar.MISSING_FILENAME_TEXT)

        # Store session cookies with `expires` set to 0 instead of an empty
        # string
        for cookie in self:
            if cookie.expires is None:
                cookie.expires = 0

        with io.open(filename, 'w', encoding='utf-8') as f:
            f.write(self._HEADER)
            now = time.time()
            for cookie in self:
                if not ignore_discard and cookie.discard:
                    continue
                if not ignore_expires and cookie.is_expired(now):
                    continue
                if cookie.secure:
                    secure = 'TRUE'
                else:
                    secure = 'FALSE'
                if cookie.domain.startswith('.'):
                    initial_dot = 'TRUE'
                else:
                    initial_dot = 'FALSE'
                if cookie.expires is not None:
                    expires = compat_str(cookie.expires)
                else:
                    expires = ''
                if cookie.value is None:
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas http.cookiejar regards it as a
                    # cookie with no value.
                    name = ''
                    value = cookie.name
                else:
                    name = cookie.name
                    value = cookie.value
                f.write(
                    '\t'.join([cookie.domain, initial_dot, cookie.path,
                               secure, expires, name, value]) + '\n')