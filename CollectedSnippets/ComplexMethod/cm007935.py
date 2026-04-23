def test_unsupported_cache_spec_no_fallback(self, memorypcp, pot_request, ie, logger):
        unsupported_provider = UnsupportedCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        cache = PoTokenCache(
            cache_providers=[memorypcp],
            cache_spec_providers=[unsupported_provider],
            logger=logger,
        )

        response = PoTokenResponse(EXAMPLE_PO_TOKEN)
        assert cache.get(pot_request) is None
        assert unsupported_provider.generate_called_times == 1
        cache.store(pot_request, response)
        assert len(memorypcp.cache) == 0
        assert unsupported_provider.generate_called_times == 2
        assert cache.get(pot_request) is None
        assert unsupported_provider.generate_called_times == 3
        assert len(logger.messages.get('error', [])) == 0