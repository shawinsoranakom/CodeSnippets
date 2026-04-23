def test_create_provider_example(self, ie, pot_request, logger):
        provider = ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        assert provider.PROVIDER_NAME == 'example'
        assert provider.PROVIDER_KEY == 'ExampleCacheSpecProvider'
        assert provider.PROVIDER_VERSION == '0.0.1'
        assert provider.BUG_REPORT_MESSAGE == 'please report this issue to the provider developer at  https://example.com/issues  .'
        assert provider.is_available()
        assert provider.generate_cache_spec(pot_request)
        assert provider.generate_cache_spec(pot_request).key_bindings == {'field': 'example-key'}
        assert provider.generate_cache_spec(pot_request).default_ttl == 60
        assert provider.generate_cache_spec(pot_request).write_policy == CacheProviderWritePolicy.WRITE_FIRST