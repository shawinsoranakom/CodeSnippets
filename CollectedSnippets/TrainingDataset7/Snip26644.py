def test_dont_set_if_set(self):
        """
        If the X-Frame-Options header is already set then the middleware does
        not attempt to override it.
        """

        def same_origin_response(request):
            response = HttpResponse()
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            return response

        def deny_response(request):
            response = HttpResponse()
            response.headers["X-Frame-Options"] = "DENY"
            return response

        with override_settings(X_FRAME_OPTIONS="DENY"):
            r = XFrameOptionsMiddleware(same_origin_response)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")

        with override_settings(X_FRAME_OPTIONS="SAMEORIGIN"):
            r = XFrameOptionsMiddleware(deny_response)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")