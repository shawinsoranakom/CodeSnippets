def test_samesite_session_cookie(self):
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(self.get_response_touching_session)
        response = middleware(request)
        self.assertEqual(
            response.cookies[settings.SESSION_COOKIE_NAME]["samesite"], "Strict"
        )