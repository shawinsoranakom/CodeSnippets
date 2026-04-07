def test_httponly_session_cookie(self):
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(self.get_response_touching_session)

        # Handle the response through the middleware
        response = middleware(request)
        self.assertIs(response.cookies[settings.SESSION_COOKIE_NAME]["httponly"], True)
        self.assertIn(
            cookies.Morsel._reserved["httponly"],
            str(response.cookies[settings.SESSION_COOKIE_NAME]),
        )