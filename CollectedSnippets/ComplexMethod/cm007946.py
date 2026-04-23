def test_bypass_cache(self, ie, pot_request, pot_cache, logger, pot_provider):
        pot_request.bypass_cache = True

        director = PoTokenRequestDirector(logger=logger, cache=pot_cache)
        director.register_provider(pot_provider)
        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert pot_provider.request_called_times == 1
        assert pot_cache.get_calls == 0
        assert pot_cache.store_calls == 1

        # Second request, should not get from cache
        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert pot_provider.request_called_times == 2
        assert pot_cache.get_calls == 0
        assert pot_cache.store_calls == 2

        # POT is still cached, should get from cache
        pot_request.bypass_cache = False
        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert pot_provider.request_called_times == 2
        assert pot_cache.get_calls == 1
        assert pot_cache.store_calls == 2