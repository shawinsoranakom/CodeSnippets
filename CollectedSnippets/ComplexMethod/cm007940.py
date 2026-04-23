def test_cache_provider_preferences(self, pot_request, ie, logger):
        pcp_one = create_memory_pcp(ie, logger, provider_key='memory_pcp_one')
        pcp_two = create_memory_pcp(ie, logger, provider_key='memory_pcp_two')

        cache = PoTokenCache(
            cache_providers=[pcp_one, pcp_two],
            cache_spec_providers=[ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})],
            logger=logger,
        )

        cache.store(pot_request, PoTokenResponse(EXAMPLE_PO_TOKEN), write_policy=CacheProviderWritePolicy.WRITE_FIRST)
        assert len(pcp_one.cache) == 1
        assert len(pcp_two.cache) == 0

        assert cache.get(pot_request)
        assert pcp_one.get_calls == 1
        assert pcp_two.get_calls == 0

        standard_preference_called = False
        pcp_one_preference_claled = False

        def standard_preference(provider, request, *_, **__):
            nonlocal standard_preference_called
            standard_preference_called = True
            assert isinstance(provider, PoTokenCacheProvider)
            assert isinstance(request, PoTokenRequest)
            return 1

        def pcp_one_preference(provider, request, *_, **__):
            nonlocal pcp_one_preference_claled
            pcp_one_preference_claled = True
            assert isinstance(provider, PoTokenCacheProvider)
            assert isinstance(request, PoTokenRequest)
            if provider.PROVIDER_KEY == pcp_one.PROVIDER_KEY:
                return -100
            return 0

        # test that it can hanldle multiple preferences
        cache.cache_provider_preferences.append(standard_preference)
        cache.cache_provider_preferences.append(pcp_one_preference)

        cache.store(pot_request, PoTokenResponse(EXAMPLE_PO_TOKEN), write_policy=CacheProviderWritePolicy.WRITE_FIRST)
        assert cache.get(pot_request)
        assert len(pcp_one.cache) == len(pcp_two.cache) == 1
        assert pcp_two.get_calls == pcp_one.get_calls == 1
        assert pcp_one.store_calls == pcp_two.store_calls == 1
        assert standard_preference_called
        assert pcp_one_preference_claled