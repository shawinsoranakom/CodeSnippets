def _perform_login(self, username, password):
        def is_logged_in():
            res = self._download_json(
                'https://www.vidio.com/interactions.json', None, 'Checking if logged in', fatal=False) or {}
            return bool(res.get('current_user'))

        if is_logged_in():
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading log in page')

        login_form = self._form_hidden_inputs('login-form', login_page)
        login_form.update({
            'user[login]': username,
            'user[password]': password,
        })
        login_post, login_post_urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Logging in', data=urlencode_postdata(login_form), expected_status=[302, 401])

        if login_post_urlh.status == 401:
            if get_element_by_class('onboarding-content-register-popup__title', login_post):
                raise ExtractorError(
                    'Unable to log in: The provided email has not registered yet.', expected=True)

            reason = get_element_by_class('onboarding-form__general-error', login_post) or get_element_by_class('onboarding-modal__title', login_post)
            if 'Akun terhubung ke' in reason:
                raise ExtractorError(
                    'Unable to log in: Your account is linked to a social media account. '
                    'Use --cookies to provide account credentials instead', expected=True)
            elif reason:
                subreason = get_element_by_class('onboarding-modal__description-text', login_post) or ''
                raise ExtractorError(
                    f'Unable to log in: {reason}. {clean_html(subreason)}', expected=True)
            raise ExtractorError('Unable to log in')