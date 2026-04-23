def test_request_and_cache(self, ie, pot_request, pot_cache, pot_provider, logger):
        director = PoTokenRequestDirector(logger=logger, cache=pot_cache)
        director.register_provider(pot_provider)
        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert pot_provider.request_called_times == 1
        assert pot_cache.get_calls == 1
        assert pot_cache.store_calls == 1

        # Second request, should be cached
        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert pot_cache.get_calls == 2
        assert pot_cache.store_calls == 1
        assert pot_provider.request_called_times == 1