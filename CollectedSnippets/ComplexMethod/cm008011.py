def _load_cookies(self, data, *, autoscope=True):
        """Loads cookies from a `Cookie` header

        This tries to work around the security vulnerability of passing cookies to every domain.
        See: https://github.com/yt-dlp/yt-dlp/security/advisories/GHSA-v8mc-9377-rwjj

        @param data         The Cookie header as string to load the cookies from
        @param autoscope    If `False`, scope cookies using Set-Cookie syntax and error for cookie without domains
                            If `True`, save cookies for later to be stored in the jar with a limited scope
                            If a URL, save cookies in the jar with the domain of the URL
        """
        for cookie in LenientSimpleCookie(data).values():
            if autoscope and any(cookie.values()):
                raise ValueError('Invalid syntax in Cookie Header')

            domain = cookie.get('domain') or ''
            expiry = cookie.get('expires')
            if expiry == '':  # 0 is valid
                expiry = None
            prepared_cookie = http.cookiejar.Cookie(
                cookie.get('version') or 0, cookie.key, cookie.value, None, False,
                domain, True, True, cookie.get('path') or '', bool(cookie.get('path')),
                cookie.get('secure') or False, expiry, False, None, None, {})

            if domain:
                self.cookiejar.set_cookie(prepared_cookie)
            elif autoscope is True:
                self.deprecated_feature(
                    'Passing cookies as a header is a potential security risk; '
                    'they will be scoped to the domain of the downloaded urls. '
                    'Please consider loading cookies from a file or browser instead.')
                self.__header_cookies.append(prepared_cookie)
            elif autoscope:
                self.report_warning(
                    'The extractor result contains an unscoped cookie as an HTTP header. '
                    f'If you are using yt-dlp with an input URL{bug_reports_message(before=",")}',
                    only_once=True)
                self._apply_header_cookies(autoscope, [prepared_cookie])
            else:
                self.report_error('Unscoped cookies are not allowed; please specify some sort of scoping',
                                  tb=False, is_error=False)