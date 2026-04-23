def test_session_delete_on_end(self):
        def response_ending_session(request):
            request.session.flush()
            return HttpResponse("Session test")

        request = self.request_factory.get("/")
        middleware = SessionMiddleware(response_ending_session)

        # Before deleting, there has to be an existing cookie
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "abc"

        # Handle the response through the middleware
        response = middleware(request)

        # The cookie was deleted, not recreated.
        # A deleted cookie header looks like:
        #  "Set-Cookie: sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; "
        #  "Max-Age=0; Path=/"
        self.assertEqual(
            'Set-Cookie: {}=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; '
            "Max-Age=0; Path=/; SameSite={}".format(
                settings.SESSION_COOKIE_NAME,
                settings.SESSION_COOKIE_SAMESITE,
            ),
            str(response.cookies[settings.SESSION_COOKIE_NAME]),
        )
        # SessionMiddleware sets 'Vary: Cookie' to prevent the 'Set-Cookie'
        # from being cached.
        self.assertEqual(response.headers["Vary"], "Cookie")