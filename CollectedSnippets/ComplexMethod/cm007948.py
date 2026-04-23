def test_unavailable_request_fallback(self, ie, logger, pot_cache, pot_request, pot_provider):
        # Should fallback to the next provider if the first one is unavailable
        director = PoTokenRequestDirector(logger=logger, cache=pot_cache)
        provider = UnavailablePTP(ie, logger, {})
        director.register_provider(provider)
        director.register_provider(pot_provider)

        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert provider.request_called_times == 0
        assert provider.available_called_times
        assert pot_provider.request_called_times == 1
        assert pot_provider.available_called_times
        # should not even try use the provider for the request
        assert 'Attempting to fetch a PO Token from "unavailable" provider' not in logger.messages['trace']
        assert 'Attempting to fetch a PO Token from "success" provider' in logger.messages['trace']