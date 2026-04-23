def test_login_csrf_rotate(self):
        """
        Makes sure that a login rotates the currently-used CSRF token.
        """

        def get_response(request):
            return HttpResponse()

        # Do a GET to establish a CSRF token
        # The test client isn't used here as it's a test for middleware.
        req = HttpRequest()
        CsrfViewMiddleware(get_response).process_view(req, LoginView.as_view(), (), {})
        # get_token() triggers CSRF token inclusion in the response
        get_token(req)
        resp = CsrfViewMiddleware(LoginView.as_view())(req)
        csrf_cookie = resp.cookies.get(settings.CSRF_COOKIE_NAME, None)
        token1 = csrf_cookie.coded_value

        # Prepare the POST request
        req = HttpRequest()
        req.COOKIES[settings.CSRF_COOKIE_NAME] = token1
        req.method = "POST"
        req.POST = {
            "username": "testclient",
            "password": "password",
            "csrfmiddlewaretoken": token1,
        }

        # Use POST request to log in
        SessionMiddleware(get_response).process_request(req)
        CsrfViewMiddleware(get_response).process_view(req, LoginView.as_view(), (), {})
        req.META["SERVER_NAME"] = (
            "testserver"  # Required to have redirect work in login view
        )
        req.META["SERVER_PORT"] = 80
        resp = CsrfViewMiddleware(LoginView.as_view())(req)
        csrf_cookie = resp.cookies.get(settings.CSRF_COOKIE_NAME, None)
        token2 = csrf_cookie.coded_value

        # Check the CSRF token switched
        self.assertNotEqual(token1, token2)