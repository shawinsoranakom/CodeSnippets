def test_session_update_error_redirect(self):
        def response_delete_session(request):
            request.session = DatabaseSession()
            request.session.save(must_create=True)
            request.session.delete()
            return HttpResponse()

        request = self.request_factory.get("/foo/")
        middleware = SessionMiddleware(response_delete_session)

        msg = (
            "The request's session was deleted before the request completed. "
            "The user may have logged out in a concurrent request, for example."
        )
        with self.assertRaisesMessage(SessionInterrupted, msg):
            # Handle the response through the middleware. It will try to save
            # the deleted session which will cause an UpdateError that's caught
            # and raised as a SessionInterrupted.
            middleware(request)