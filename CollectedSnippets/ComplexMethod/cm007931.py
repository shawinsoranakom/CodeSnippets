def test_create_provider_barebones(self, ie, pot_request, logger):
        class BarebonesProviderPCSP(PoTokenCacheSpecProvider):
            def generate_cache_spec(self, request: PoTokenRequest):
                return PoTokenCacheSpec(
                    default_ttl=100,
                    key_bindings={},
                )

        provider = BarebonesProviderPCSP(ie=ie, logger=logger, settings={})
        assert provider.PROVIDER_NAME == 'BarebonesProvider'
        assert provider.PROVIDER_KEY == 'BarebonesProvider'
        assert provider.PROVIDER_VERSION == '0.0.0'
        assert provider.BUG_REPORT_MESSAGE == 'please report this issue to the provider developer at  (developer has not provided a bug report location)  .'
        assert provider.is_available()
        assert provider.generate_cache_spec(request=pot_request).default_ttl == 100
        assert provider.generate_cache_spec(request=pot_request).key_bindings == {}
        assert provider.generate_cache_spec(request=pot_request).write_policy == CacheProviderWritePolicy.WRITE_ALL