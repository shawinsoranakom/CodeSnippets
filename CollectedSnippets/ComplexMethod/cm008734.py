def get(self, request: PoTokenRequest) -> PoTokenResponse | None:
        spec = self._get_cache_spec(request)
        if not spec:
            self.logger.trace('No cache spec available for this request, unable to fetch from cache')
            return None

        cache_key = self._generate_key(self._generate_key_bindings(spec))
        self.logger.trace(f'Attempting to access PO Token cache using key: {cache_key}')

        for idx, provider in enumerate(self._get_cache_providers(request)):
            try:
                self.logger.trace(
                    f'Attempting to fetch PO Token response from "{provider.PROVIDER_NAME}" cache provider')
                cache_response = provider.get(cache_key)
                if not cache_response:
                    continue
                try:
                    po_token_response = PoTokenResponse(**json.loads(cache_response))
                except (TypeError, ValueError, json.JSONDecodeError):
                    po_token_response = None
                if not validate_response(po_token_response):
                    self.logger.error(
                        f'Invalid PO Token response retrieved from cache provider "{provider.PROVIDER_NAME}": '
                        f'{cache_response}{provider_bug_report_message(provider)}')
                    provider.delete(cache_key)
                    continue
                self.logger.trace(
                    f'PO Token response retrieved from cache using "{provider.PROVIDER_NAME}" provider: '
                    f'{po_token_response}')
                if idx > 0:
                    # Write back to the highest priority cache provider,
                    # so we stop trying to fetch from lower priority providers
                    self.logger.trace('Writing PO Token response to highest priority cache provider')
                    self.store(request, po_token_response, write_policy=CacheProviderWritePolicy.WRITE_FIRST)

                return po_token_response
            except PoTokenCacheProviderError as e:
                self.logger.warning(
                    f'Error from "{provider.PROVIDER_NAME}" PO Token cache provider: '
                    f'{e!r}{provider_bug_report_message(provider) if not e.expected else ""}')
                continue
            except Exception as e:
                self.logger.error(
                    f'Error occurred with "{provider.PROVIDER_NAME}" PO Token cache provider: '
                    f'{e!r}{provider_bug_report_message(provider)}',
                )
                continue
        return None