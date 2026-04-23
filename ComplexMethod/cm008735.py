def store(
        self,
        request: PoTokenRequest,
        response: PoTokenResponse,
        write_policy: CacheProviderWritePolicy | None = None,
    ):
        spec = self._get_cache_spec(request)
        if not spec:
            self.logger.trace('No cache spec available for this request. Not caching.')
            return

        if not validate_response(response):
            self.logger.error(
                f'Invalid PO Token response provided to PoTokenCache.store(): '
                f'{response}{bug_reports_message()}')
            return

        cache_key = self._generate_key(self._generate_key_bindings(spec))
        self.logger.trace(f'Attempting to access PO Token cache using key: {cache_key}')

        default_expires_at = int(dt.datetime.now(dt.timezone.utc).timestamp()) + spec.default_ttl
        cache_response = dataclasses.replace(response, expires_at=response.expires_at or default_expires_at)

        write_policy = write_policy or spec.write_policy
        self.logger.trace(f'Using write policy: {write_policy}')

        for idx, provider in enumerate(self._get_cache_providers(request)):
            try:
                self.logger.trace(
                    f'Caching PO Token response in "{provider.PROVIDER_NAME}" cache provider '
                    f'(key={cache_key}, expires_at={cache_response.expires_at})')
                provider.store(
                    key=cache_key,
                    value=json.dumps(dataclasses.asdict(cache_response)),
                    expires_at=cache_response.expires_at)
            except PoTokenCacheProviderError as e:
                self.logger.warning(
                    f'Error from "{provider.PROVIDER_NAME}" PO Token cache provider: '
                    f'{e!r}{provider_bug_report_message(provider) if not e.expected else ""}')
            except Exception as e:
                self.logger.error(
                    f'Error occurred with "{provider.PROVIDER_NAME}" PO Token cache provider: '
                    f'{e!r}{provider_bug_report_message(provider)}')

            # WRITE_FIRST should not write to lower priority providers in the case the highest priority provider fails
            if idx == 0 and write_policy == CacheProviderWritePolicy.WRITE_FIRST:
                return