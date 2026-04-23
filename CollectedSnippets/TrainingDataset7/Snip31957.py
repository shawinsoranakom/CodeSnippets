def test_no_httponly_session_cookie(self):
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(self.get_response_touching_session)
        response = middleware(request)
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]["httponly"], "")
        self.assertNotIn(
            cookies.Morsel._reserved["httponly"],
            str(response.cookies[settings.SESSION_COOKIE_NAME]),
        )