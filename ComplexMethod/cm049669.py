def _check_credentials(self, credential, env):
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if not (credential['type'] == 'password' and credential.get('password')):
                raise
            passwd_allowed = env['interactive'] or not self.env.user._rpc_api_keys_only()
            if passwd_allowed and self.env.user.active:
                Ldap = self.env['res.company.ldap']
                for conf in Ldap._get_ldap_dicts():
                    if Ldap._authenticate(conf, self.env.user.login, credential['password']):
                        return {
                            'uid': self.env.user.id,
                            'auth_method': 'ldap',
                            'mfa': 'default',
                        }
            raise