def _load_cookies(self, data, **kwargs):
        """Loads cookies from a `Cookie` header

        This tries to work around the security vulnerability of passing cookies to every domain.

        @param data         The Cookie header as a string to load the cookies from
        @param autoscope    If `False`, scope cookies using Set-Cookie syntax and error for cookie without domains
                            If `True`, save cookies for later to be stored in the jar with a limited scope
                            If a URL, save cookies in the jar with the domain of the URL
        """
        # autoscope=True (kw-only)
        autoscope = kwargs.get('autoscope', True)

        for cookie in compat_http_cookies_SimpleCookie(data).values() if data else []:
            if autoscope and any(cookie.values()):
                raise ValueError('Invalid syntax in Cookie Header')

            domain = cookie.get('domain') or ''
            expiry = cookie.get('expires')
            if expiry == '':  # 0 is valid so we check for `''` explicitly
                expiry = None
            prepared_cookie = compat_http_cookiejar_Cookie(
                cookie.get('version') or 0, cookie.key, cookie.value, None, False,
                domain, True, True, cookie.get('path') or '', bool(cookie.get('path')),
                bool(cookie.get('secure')), expiry, False, None, None, {})

            if domain:
                self.cookiejar.set_cookie(prepared_cookie)
            elif autoscope is True:
                self.report_warning(
                    'Passing cookies as a header is a potential security risk; '
                    'they will be scoped to the domain of the downloaded urls. '
                    'Please consider loading cookies from a file or browser instead.',
                    only_once=True)
                self._header_cookies.append(prepared_cookie)
            elif autoscope:
                self.report_warning(
                    'The extractor result contains an unscoped cookie as an HTTP header. '
                    'If you are specifying an input URL, ' + bug_reports_message(),
                    only_once=True)
                self._apply_header_cookies(autoscope, [prepared_cookie])
            else:
                self.report_unscoped_cookies()