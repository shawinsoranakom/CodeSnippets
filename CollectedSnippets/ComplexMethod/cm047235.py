def _check_credentials(self, credential, env):
        """ Validates the current user's password.

        Override this method to plug additional authentication methods.

        Overrides should:

        * call ``super`` to delegate to parents for credentials-checking
        * catch :class:`~odoo.exceptions.AccessDenied` and perform their
          own checking
        * (re)raise :class:`~odoo.exceptions.AccessDenied` if the
          credentials are still invalid according to their own
          validation method
        * return the ``auth_info``

        When trying to check for credentials validity, call
        :meth:`_check_credentials` instead.

        Credentials are considered to be untrusted user input, for more
        information please check :meth:`authenticate`

        :returns: ``auth_info`` dictionary containing:

          - uid: the uid of the authenticated user
          - auth_method: which method was used during authentication
          - mfa: whether mfa should be skipped or not, possible values:

            - enforce: enforce mfa no matter what (not yet implemented)
            - default: delegate to auth_totp
            - skip: skip mfa no matter what

          Examples:

          - ``{ 'uid': 20, 'auth_method': 'password',      'mfa': 'default' }``
          - ``{ 'uid': 17, 'auth_method': 'impersonation', 'mfa': 'enforce' }``
          - ``{ 'uid': 32, 'auth_method': 'webauthn',      'mfa': 'skip'    }``
        :rtype: dict
        """
        if not (credential['type'] == 'password' and credential.get('password')):
            raise AccessDenied()

        env = env or {}
        interactive = env.get('interactive', True)

        if interactive or not self.env.user._rpc_api_keys_only():
            if 'interactive' not in env:
                _logger.warning(
                    "_check_credentials without 'interactive' env key, assuming interactive login. \
                    Check calls and overrides to ensure the 'interactive' key is properly set in \
                    all _check_credentials environments"
                )

            self.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [self.env.user.id]
            )
            [hashed] = self.env.cr.fetchone()
            valid, replacement = self._crypt_context()\
                .verify_and_update(credential['password'], hashed)
            if replacement is not None:
                self._set_encrypted_password(self.env.user.id, replacement)
                if request and self == self.env.user:
                    self.env.flush_all()
                    self.env.registry.clear_cache()
                    # update session token so the user does not get logged out
                    new_token = self.env.user._compute_session_token(request.session.sid)
                    request.session.session_token = new_token

            if valid:
                return {
                    'uid': self.env.user.id,
                    'auth_method': 'password',
                    'mfa': 'default',
                }

        if not interactive:
            # 'rpc' scope does not really exist, we basically require a global key (scope NULL)
            if self.env['res.users.apikeys']._check_credentials(scope='rpc', key=credential['password']) == self.env.uid:
                return {
                    'uid': self.env.user.id,
                    'auth_method': 'apikey',
                    'mfa': 'default',
                }

            if self.env.user._rpc_api_keys_only():
                _logger.info(
                    "Invalid API key or password-based authentication attempted for a non-interactive (API) "
                    "context that requires API key authentication only."
                )

        raise AccessDenied()