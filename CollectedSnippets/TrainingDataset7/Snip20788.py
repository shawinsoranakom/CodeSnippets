def test_csp_report_only_override(self):
        @csp_report_only_override(basic_config)
        def sync_view(request):
            return HttpResponse("OK")

        response = sync_view(HttpRequest())
        self.assertEqual(response._csp_ro_config, basic_config)
        self.assertIs(hasattr(response, "_csp_config"), False)