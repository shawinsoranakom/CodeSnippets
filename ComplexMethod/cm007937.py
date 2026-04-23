def test_invalid_cache_spec_fallback(self, memorypcp, pot_request, ie, logger):

        invalid_provider = InvalidSpecCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        example_provider = ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        cache = PoTokenCache(
            cache_providers=[memorypcp],
            cache_spec_providers=[invalid_provider, example_provider],
            logger=logger,
        )

        response = PoTokenResponse(EXAMPLE_PO_TOKEN)

        assert cache.get(pot_request) is None
        assert invalid_provider.generate_called_times == example_provider.generate_called_times == 1

        cache.store(pot_request, response)
        assert invalid_provider.generate_called_times == example_provider.generate_called_times == 2

        cached_response = cache.get(pot_request)
        assert invalid_provider.generate_called_times == example_provider.generate_called_times == 3
        assert cached_response is not None
        assert cached_response.po_token == EXAMPLE_PO_TOKEN
        assert cached_response.expires_at is not None

        assert 'PoTokenCacheSpecProvider "InvalidSpecCacheSpecProvider" generate_cache_spec() returned invalid spec invalid-spec; please report this issue to the provider developer at  (developer has not provided a bug report location)  .' in logger.messages['error']