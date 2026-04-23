def _get_user_token(self):
        username, password = self._get_login_info()
        if not username or not password:
            return

        user_token = IwaraBaseIE._USERTOKEN or self.cache.load(self._NETRC_MACHINE, username)
        if not user_token or self._is_token_expired(user_token, 'User'):
            response = self._download_json(
                'https://api.iwara.tv/user/login', None, note='Logging in',
                headers={'Content-Type': 'application/json'}, data=json.dumps({
                    'email': username,
                    'password': password,
                }).encode(), expected_status=lambda x: True)
            user_token = traverse_obj(response, ('token', {str}))
            if not user_token:
                error = traverse_obj(response, ('message', {str}))
                if 'invalidLogin' in error:
                    raise ExtractorError('Invalid login credentials', expected=True)
                else:
                    raise ExtractorError(f'Iwara API said: {error or "nothing"}')

            self.cache.store(self._NETRC_MACHINE, username, user_token)

        IwaraBaseIE._USERTOKEN = user_token