def test_empty_session_saved(self):
        """
        If a session is emptied of data but still has a key, it should still
        be updated.
        """

        def response_set_session(request):
            # Set a session key and some data.
            request.session["foo"] = "bar"
            return HttpResponse("Session test")

        request = self.request_factory.get("/")
        middleware = SessionMiddleware(response_set_session)

        # Handle the response through the middleware.
        response = middleware(request)
        self.assertEqual(tuple(request.session.items()), (("foo", "bar"),))
        # A cookie should be set, along with Vary: Cookie.
        self.assertIn(
            "Set-Cookie: sessionid=%s" % request.session.session_key,
            str(response.cookies),
        )
        self.assertEqual(response.headers["Vary"], "Cookie")

        # Empty the session data.
        del request.session["foo"]
        # Handle the response through the middleware.
        response = HttpResponse("Session test")
        response = middleware.process_response(request, response)
        self.assertEqual(dict(request.session.values()), {})
        session = Session.objects.get(session_key=request.session.session_key)
        self.assertEqual(session.get_decoded(), {})
        # While the session is empty, it hasn't been flushed so a cookie should
        # still be set, along with Vary: Cookie.
        self.assertGreater(len(request.session.session_key), 8)
        self.assertIn(
            "Set-Cookie: sessionid=%s" % request.session.session_key,
            str(response.cookies),
        )
        self.assertEqual(response.headers["Vary"], "Cookie")