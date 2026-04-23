def test_get_invalid_po_token_response(self, pot_request, ie, logger):
        # Test various scenarios where the po token response stored in the cache provider is invalid
        pcp_one = create_memory_pcp(ie, logger, provider_key='memory_pcp_one')
        pcp_two = create_memory_pcp(ie, logger, provider_key='memory_pcp_two')

        cache = PoTokenCache(
            cache_providers=[pcp_one, pcp_two],
            cache_spec_providers=[ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})],
            logger=logger,
        )

        valid_response = PoTokenResponse(EXAMPLE_PO_TOKEN)
        cache.store(pot_request, valid_response)
        assert len(pcp_one.cache) == len(pcp_two.cache) == 1
        # Overwrite the valid response with an invalid one in the cache
        pcp_one.store(next(iter(pcp_one.cache.keys())), json.dumps(dataclasses.asdict(PoTokenResponse(None))), int(time.time() + 1000))
        assert cache.get(pot_request).po_token == valid_response.po_token
        assert pcp_one.get_calls == pcp_two.get_calls == 1
        assert pcp_one.delete_calls == 1  # Invalid response should be deleted from cache
        assert pcp_one.store_calls == 3  # Since response was fetched from second cache provider, it should be stored in the first one
        assert len(pcp_one.cache) == 1
        assert 'Invalid PO Token response retrieved from cache provider "memory": {"po_token": null, "expires_at": null}; example bug report message' in logger.messages['error']

        # Overwrite the valid response with an invalid json in the cache
        pcp_one.store(next(iter(pcp_one.cache.keys())), 'invalid-json', int(time.time() + 1000))
        assert cache.get(pot_request).po_token == valid_response.po_token
        assert pcp_one.get_calls == pcp_two.get_calls == 2
        assert pcp_one.delete_calls == 2
        assert pcp_one.store_calls == 5  # 3 + 1 store we made in the test + 1 store from lower priority cache provider
        assert len(pcp_one.cache) == 1

        assert 'Invalid PO Token response retrieved from cache provider "memory": invalid-json; example bug report message' in logger.messages['error']

        # Valid json, but missing required fields
        pcp_one.store(next(iter(pcp_one.cache.keys())), '{"unknown_param": 0}', int(time.time() + 1000))
        assert cache.get(pot_request).po_token == valid_response.po_token
        assert pcp_one.get_calls == pcp_two.get_calls == 3
        assert pcp_one.delete_calls == 3
        assert pcp_one.store_calls == 7  # 5 + 1 store from test + 1 store from lower priority cache provider
        assert len(pcp_one.cache) == 1

        assert 'Invalid PO Token response retrieved from cache provider "memory": {"unknown_param": 0}; example bug report message' in logger.messages['error']