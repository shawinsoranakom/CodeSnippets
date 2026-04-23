def _login(self, site):
        if self._logged_in:
            return

        username, password = self._get_login_info(netrc_machine=self._SITES.get(site, site))
        if username is None:
            return

        login_page, urlh = self._download_webpage_handle(
            f'https://{site}/sign_in', None,
            f'Downloading {site} login page')

        def is_logged(webpage):
            return any(re.search(p, webpage) for p in (
                r'class=["\']user-signout',
                r'<a[^>]+\bhref=["\']/sign_out',
                r'Log\s+[Oo]ut\s*<'))

        if is_logged(login_page):
            self._logged_in = True
            return

        login_url = urlh.url

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'user[email]': username,
            'user[password]': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>(?:(?!\1).)+)\1', login_page,
            'post url', default=login_url, group='url')

        if not post_url.startswith('http'):
            post_url = urljoin(login_url, post_url)

        response = self._download_webpage(
            post_url, None, f'Logging in to {site}',
            data=urlencode_postdata(login_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
            })

        if '>I accept the new Privacy Policy<' in response:
            raise ExtractorError(
                f'Unable to login: {site} asks you to accept new Privacy Policy. '
                f'Go to https://{site}/ and accept.', expected=True)

        # Successful login
        if is_logged(response):
            self._logged_in = True
            return

        message = get_element_by_class('alert', response)
        if message is not None:
            raise ExtractorError(
                f'Unable to login: {clean_html(message)}', expected=True)

        raise ExtractorError('Unable to log in')