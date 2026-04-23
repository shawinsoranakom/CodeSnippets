def _perform_login(self, username, password):
        _, urlh = self._download_webpage_handle(
            'https://learning.oreilly.com/accounts/login-check/', None,
            'Downloading login page')

        def is_logged(urlh):
            return 'learning.oreilly.com/home/' in urlh.url

        if is_logged(urlh):
            self.LOGGED_IN = True
            return

        redirect_url = urlh.url
        parsed_url = urllib.parse.urlparse(redirect_url)
        qs = urllib.parse.parse_qs(parsed_url.query)
        next_uri = urllib.parse.urljoin(
            'https://api.oreilly.com', qs['next'][0])

        auth, urlh = self._download_json_handle(
            'https://www.oreilly.com/member/auth/login/', None, 'Logging in',
            data=json.dumps({
                'email': username,
                'password': password,
                'redirect_uri': next_uri,
            }).encode(), headers={
                'Content-Type': 'application/json',
                'Referer': redirect_url,
            }, expected_status=400)

        credentials = auth.get('credentials')
        if (not auth.get('logged_in') and not auth.get('redirect_uri')
                and credentials):
            raise ExtractorError(
                f'Unable to login: {credentials}', expected=True)

        # oreilly serves two same instances of the following cookies
        # in Set-Cookie header and expects first one to be actually set
        for cookie in ('groot_sessionid', 'orm-jwt', 'orm-rt'):
            self._apply_first_set_cookie_header(urlh, cookie)

        _, urlh = self._download_webpage_handle(
            auth.get('redirect_uri') or next_uri, None, 'Completing login')

        if is_logged(urlh):
            self.LOGGED_IN = True
            return

        raise ExtractorError('Unable to log in')