async def test_csp_override_async_view(self):
        @csp_override(basic_config)
        async def async_view(request):
            return HttpResponse("OK")

        response = await async_view(HttpRequest())
        self.assertEqual(response._csp_config, basic_config)
        self.assertIs(hasattr(response, "_csp_ro_config"), False)