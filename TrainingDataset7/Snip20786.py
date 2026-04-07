def test_csp_override(self):
        @csp_override(basic_config)
        def sync_view(request):
            return HttpResponse("OK")

        response = sync_view(HttpRequest())
        self.assertEqual(response._csp_config, basic_config)
        self.assertIs(hasattr(response, "_csp_ro_config"), False)