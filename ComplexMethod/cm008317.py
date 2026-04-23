def _perform_login(self, username, password):
        if self.is_logged_in:
            return

        self._request_webpage(
            f'{self._LOGIN_BASE}/login', None, 'Requesting session cookies')
        webpage = self._download_webpage(
            f'{self._LOGIN_BASE}/login/redirector', None,
            'Logging in', 'Unable to log in', headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f'{self._LOGIN_BASE}/login',
            }, data=urlencode_postdata({
                'mail_tel': username,
                'password': password,
            }))

        if self.is_logged_in:
            return
        elif err_msg := traverse_obj(webpage, (
            {find_element(cls='notice error')}, {find_element(cls='notice__text')}, {clean_html},
        )):
            self._raise_login_error(err_msg or 'Invalid username or password')
        elif 'oneTimePw' in webpage:
            post_url = self._search_regex(
                r'<form[^>]+action=(["\'])(?P<url>.+?)\1', webpage, 'post url', group='url')
            mfa, urlh = self._download_webpage_handle(
                urljoin(self._LOGIN_BASE, post_url), None,
                'Performing MFA', 'Unable to complete MFA', headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }, data=urlencode_postdata({
                    'otp': self._get_tfa_info('6 digit number shown on app'),
                }))
            if self.is_logged_in:
                return
            elif 'error-code' in parse_qs(urlh.url):
                err_msg = traverse_obj(mfa, ({find_element(cls='pageMainMsg')}, {clean_html}))
                self._raise_login_error(err_msg or 'MFA session expired')
            elif 'formError' in mfa:
                err_msg = traverse_obj(mfa, (
                    {find_element(cls='formError')}, {find_element(tag='div')}, {clean_html}))
                self._raise_login_error(err_msg or 'MFA challenge failed')

        self._raise_login_error('Unexpected login error', expected=False)