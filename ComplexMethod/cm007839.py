def _login(self):
        """
        Attempt to log in to YouTube.

        True is returned if successful or skipped.
        False is returned if login failed.

        If _LOGIN_REQUIRED is set and no authentication was provided, an error is raised.
        """
        username, password = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED and self._downloader.params.get('cookiefile') is None:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return True

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='unable to fetch login page', fatal=False)
        if login_page is False:
            return

        login_form = self._hidden_inputs(login_page)

        def req(url, f_req, note, errnote):
            data = login_form.copy()
            data.update({
                'pstMsg': 1,
                'checkConnection': 'youtube',
                'checkedDomains': 'youtube',
                'hl': 'en',
                'deviceinfo': '[null,null,null,[],null,"US",null,null,[],"GlifWebSignIn",null,[null,null,[]]]',
                'f.req': json.dumps(f_req),
                'flowName': 'GlifWebSignIn',
                'flowEntry': 'ServiceLogin',
                # TODO: reverse actual botguard identifier generation algo
                'bgRequest': '["identifier",""]',
            })
            return self._download_json(
                url, None, note=note, errnote=errnote,
                transform_source=lambda s: re.sub(r'^[^[]*', '', s),
                fatal=False,
                data=urlencode_postdata(data), headers={
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
                    'Google-Accounts-XSRF': 1,
                })

        def warn(message):
            self._downloader.report_warning(message)

        lookup_req = [
            username,
            None, [], None, 'US', None, None, 2, False, True,
            [
                None, None,
                [2, 1, None, 1,
                 'https://accounts.google.com/ServiceLogin?passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26action_handle_signin%3Dtrue%26hl%3Den%26app%3Ddesktop%26feature%3Dsign_in_button&hl=en&service=youtube&uilel=3&requestPath=%2FServiceLogin&Page=PasswordSeparationSignIn',
                 None, [], 4],
                1, [None, None, []], None, None, None, True,
            ],
            username,
        ]

        lookup_results = req(
            self._LOOKUP_URL, lookup_req,
            'Looking up account info', 'Unable to look up account info')

        if lookup_results is False:
            return False

        user_hash = try_get(lookup_results, lambda x: x[0][2], compat_str)
        if not user_hash:
            warn('Unable to extract user hash')
            return False

        challenge_req = [
            user_hash,
            None, 1, None, [1, None, None, None, [password, None, True]],
            [
                None, None, [2, 1, None, 1, 'https://accounts.google.com/ServiceLogin?passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26action_handle_signin%3Dtrue%26hl%3Den%26app%3Ddesktop%26feature%3Dsign_in_button&hl=en&service=youtube&uilel=3&requestPath=%2FServiceLogin&Page=PasswordSeparationSignIn', None, [], 4],
                1, [None, None, []], None, None, None, True,
            ]]

        challenge_results = req(
            self._CHALLENGE_URL, challenge_req,
            'Logging in', 'Unable to log in')

        if challenge_results is False:
            return

        login_res = try_get(challenge_results, lambda x: x[0][5], list)
        if login_res:
            login_msg = try_get(login_res, lambda x: x[5], compat_str)
            warn(
                'Unable to login: %s' % 'Invalid password'
                if login_msg == 'INCORRECT_ANSWER_ENTERED' else login_msg)
            return False

        res = try_get(challenge_results, lambda x: x[0][-1], list)
        if not res:
            warn('Unable to extract result entry')
            return False

        login_challenge = try_get(res, lambda x: x[0][0], list)
        if login_challenge:
            challenge_str = try_get(login_challenge, lambda x: x[2], compat_str)
            if challenge_str == 'TWO_STEP_VERIFICATION':
                # SEND_SUCCESS - TFA code has been successfully sent to phone
                # QUOTA_EXCEEDED - reached the limit of TFA codes
                status = try_get(login_challenge, lambda x: x[5], compat_str)
                if status == 'QUOTA_EXCEEDED':
                    warn('Exceeded the limit of TFA codes, try later')
                    return False

                tl = try_get(challenge_results, lambda x: x[1][2], compat_str)
                if not tl:
                    warn('Unable to extract TL')
                    return False

                tfa_code = self._get_tfa_info('2-step verification code')

                if not tfa_code:
                    warn(
                        'Two-factor authentication required. Provide it either interactively or with --twofactor <code>'
                        '(Note that only TOTP (Google Authenticator App) codes work at this time.)')
                    return False

                tfa_code = remove_start(tfa_code, 'G-')

                tfa_req = [
                    user_hash, None, 2, None,
                    [
                        9, None, None, None, None, None, None, None,
                        [None, tfa_code, True, 2],
                    ]]

                tfa_results = req(
                    self._TFA_URL.format(tl), tfa_req,
                    'Submitting TFA code', 'Unable to submit TFA code')

                if tfa_results is False:
                    return False

                tfa_res = try_get(tfa_results, lambda x: x[0][5], list)
                if tfa_res:
                    tfa_msg = try_get(tfa_res, lambda x: x[5], compat_str)
                    warn(
                        'Unable to finish TFA: %s' % 'Invalid TFA code'
                        if tfa_msg == 'INCORRECT_ANSWER_ENTERED' else tfa_msg)
                    return False

                check_cookie_url = try_get(
                    tfa_results, lambda x: x[0][-1][2], compat_str)
            else:
                CHALLENGES = {
                    'LOGIN_CHALLENGE': "This device isn't recognized. For your security, Google wants to make sure it's really you.",
                    'USERNAME_RECOVERY': 'Please provide additional information to aid in the recovery process.',
                    'REAUTH': "There is something unusual about your activity. For your security, Google wants to make sure it's really you.",
                }
                challenge = CHALLENGES.get(
                    challenge_str,
                    '%s returned error %s.' % (self.IE_NAME, challenge_str))
                warn('%s\nGo to https://accounts.google.com/, login and solve a challenge.' % challenge)
                return False
        else:
            check_cookie_url = try_get(res, lambda x: x[2], compat_str)

        if not check_cookie_url:
            warn('Unable to extract CheckCookie URL')
            return False

        check_cookie_results = self._download_webpage(
            check_cookie_url, None, 'Checking cookie', fatal=False)

        if check_cookie_results is False:
            return False

        if 'https://myaccount.google.com/' not in check_cookie_results:
            warn('Unable to log in')
            return False

        return True