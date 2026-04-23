def test_response_exempt(self):
        """
        If the response has an xframe_options_exempt attribute set to False
        then it still sets the header, but if it's set to True then it doesn't.
        """

        def xframe_exempt_response(request):
            response = HttpResponse()
            response.xframe_options_exempt = True
            return response

        def xframe_not_exempt_response(request):
            response = HttpResponse()
            response.xframe_options_exempt = False
            return response

        with override_settings(X_FRAME_OPTIONS="SAMEORIGIN"):
            r = XFrameOptionsMiddleware(xframe_not_exempt_response)(HttpRequest())
            self.assertEqual(r.headers["X-Frame-Options"], "SAMEORIGIN")

            r = XFrameOptionsMiddleware(xframe_exempt_response)(HttpRequest())
            self.assertIsNone(r.headers.get("X-Frame-Options"))