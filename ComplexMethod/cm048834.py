def _check_credentials(self, credential, env):
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if not (credential['type'] == 'oauth_token' and credential['token']):
                raise
            passwd_allowed = env['interactive'] or not self.env.user._rpc_api_keys_only()
            if passwd_allowed and self.env.user.active:
                res = self.sudo().search([('id', '=', self.env.uid), ('oauth_access_token', '=', credential['token'])])
                if res:
                    return {
                        'uid': self.env.user.id,
                        'auth_method': 'oauth',
                        'mfa': 'default',
                    }
            raise