def test_is_extendable(self):
        """
        The XFrameOptionsMiddleware method that determines the X-Frame-Options
        header value can be overridden based on something in the request or
        response.
        """

        class OtherXFrameOptionsMiddleware(XFrameOptionsMiddleware):
            # This is just an example for testing purposes...
            def get_xframe_options_value(self, request, response):
                if getattr(request, "sameorigin", False):
                    return "SAMEORIGIN"
                if getattr(response, "sameorigin", False):
                    return "SAMEORIGIN"
                return "DENY"

        def same_origin_response(request):
            response = HttpResponse()
            response.sameorigin = True
            return response

        with override_settings(X_FRAME_OPTIONS="DENY"):
            r = OtherXFrameOptionsMiddleware(same_origin_response)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")

            request = HttpRequest()
            request.sameorigin = True
            r = OtherXFrameOptionsMiddleware(get_response_empty)(request)
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")

        with override_settings(X_FRAME_OPTIONS="SAMEORIGIN"):
            r = OtherXFrameOptionsMiddleware(get_response_empty)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")