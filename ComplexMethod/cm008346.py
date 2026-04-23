def _perform_login(self, username, password):
        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'Username': username,
            'Password': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = urllib.parse.urljoin(self._LOGIN_URL, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        error = self._search_regex(
            r'<span[^>]+class="field-validation-error"[^>]*>([^<]+)</span>',
            response, 'error message', default=None)
        if error:
            raise ExtractorError(f'Unable to login: {error}', expected=True)

        if all(not re.search(p, response) for p in (
                r'__INITIAL_STATE__', r'["\']currentUser["\']',
                # new layout?
                r'>\s*Sign out\s*<')):
            BLOCKED = 'Your account has been blocked due to suspicious activity'
            if BLOCKED in response:
                raise ExtractorError(
                    f'Unable to login: {BLOCKED}', expected=True)
            MUST_AGREE = 'To continue using Pluralsight, you must agree to'
            if any(p in response for p in (MUST_AGREE, '>Disagree<', '>Agree<')):
                raise ExtractorError(
                    f'Unable to login: {MUST_AGREE} some documents. Go to pluralsight.com, '
                    'log in and agree with what Pluralsight requires.', expected=True)

            raise ExtractorError('Unable to log in')