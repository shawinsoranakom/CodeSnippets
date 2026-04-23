def test_pot_provider_preferences(self, pot_request, pot_cache, ie, logger):
        pot_request.bypass_cache = True
        provider_two_pot = base64.urlsafe_b64encode(b'token2').decode()

        example_provider = success_ptp(response=PoTokenResponse(EXAMPLE_PO_TOKEN), key='exampleone')(ie, logger, settings={})
        example_provider_two = success_ptp(response=PoTokenResponse(provider_two_pot), key='exampletwo')(ie, logger, settings={})

        director = PoTokenRequestDirector(logger=logger, cache=pot_cache)
        director.register_provider(example_provider)
        director.register_provider(example_provider_two)

        response = director.get_po_token(pot_request)
        assert response == EXAMPLE_PO_TOKEN
        assert example_provider.request_called_times == 1
        assert example_provider_two.request_called_times == 0

        standard_preference_called = False
        example_preference_called = False

        # Test that the provider preferences are respected
        def standard_preference(provider, request, *_, **__):
            nonlocal standard_preference_called
            standard_preference_called = True
            assert isinstance(provider, PoTokenProvider)
            assert isinstance(request, PoTokenRequest)
            return 1

        def example_preference(provider, request, *_, **__):
            nonlocal example_preference_called
            example_preference_called = True
            assert isinstance(provider, PoTokenProvider)
            assert isinstance(request, PoTokenRequest)
            if provider.PROVIDER_KEY == example_provider.PROVIDER_KEY:
                return -100
            return 0

        # test that it can handle multiple preferences
        director.register_preference(example_preference)
        director.register_preference(standard_preference)

        response = director.get_po_token(pot_request)
        assert response == provider_two_pot
        assert example_provider.request_called_times == 1
        assert example_provider_two.request_called_times == 1
        assert standard_preference_called
        assert example_preference_called