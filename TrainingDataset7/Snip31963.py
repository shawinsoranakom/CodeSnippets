def test_flush_empty_without_session_cookie_doesnt_set_cookie(self):
        def response_ending_session(request):
            request.session.flush()
            return HttpResponse("Session test")

        request = self.request_factory.get("/")
        middleware = SessionMiddleware(response_ending_session)

        # Handle the response through the middleware
        response = middleware(request)

        # A cookie should not be set.
        self.assertEqual(response.cookies, {})
        # The session is accessed so "Vary: Cookie" should be set.
        self.assertEqual(response.headers["Vary"], "Cookie")