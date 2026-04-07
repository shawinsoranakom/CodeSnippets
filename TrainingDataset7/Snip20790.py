def test_csp_override_both(self):
        @csp_override(basic_config)
        @csp_report_only_override(basic_config)
        def sync_view(request):
            return HttpResponse("OK")

        response = sync_view(HttpRequest())
        self.assertEqual(response._csp_config, basic_config)
        self.assertEqual(response._csp_ro_config, basic_config)