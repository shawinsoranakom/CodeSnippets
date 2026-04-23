def test_xheader_preferred_to_underlying_request(self):
        class ProxyRequest(HttpRequest):
            def _get_scheme(self):
                """Proxy always connecting via HTTPS"""
                return "https"

        # Client connects via HTTP.
        req = ProxyRequest()
        req.META["HTTP_X_FORWARDED_PROTO"] = "http"
        self.assertIs(req.is_secure(), False)