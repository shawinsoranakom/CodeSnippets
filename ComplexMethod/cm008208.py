def _real_initialize(self):
        if self._is_logged_in:
            return

        if self._LOGIN_REQUIRED:
            self.raise_login_required()

        if self._DEFAULT_CLIENT != 'web':
            return

        for client_name, client_config in self._CLIENT_CONFIGS.items():
            if not client_config['CACHE_ONLY']:
                continue

            cache_key = client_config['CACHE_KEY']
            if cache_key not in self._oauth_tokens:
                if token := self.cache.load(self._NETRC_MACHINE, cache_key):
                    self._oauth_tokens[cache_key] = token

            if self._oauth_tokens.get(cache_key):
                self._DEFAULT_CLIENT = client_name
                self.write_debug(
                    f'Found cached {client_name} token; using {client_name} as default API client')
                return