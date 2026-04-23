def test_example_provider_success(self, ie, logger, pot_request):
        provider = ExamplePTP(ie=ie, logger=logger, settings={})
        assert provider.PROVIDER_NAME == 'example'
        assert provider.PROVIDER_KEY == 'Example'
        assert provider.PROVIDER_VERSION == '0.0.1'
        assert provider.BUG_REPORT_MESSAGE == 'please report this issue to the provider developer at  https://example.com/issues  .'
        assert provider.is_available()

        response = provider.request_pot(pot_request)

        assert response.po_token == 'example-token'
        assert response.expires_at == 123