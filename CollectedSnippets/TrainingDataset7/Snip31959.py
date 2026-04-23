def test_session_save_on_5xx(self):
        def response_503(request):
            response = HttpResponse("Service Unavailable")
            response.status_code = 503
            request.session["hello"] = "world"
            return response

        request = self.request_factory.get("/")
        SessionMiddleware(response_503)(request)

        # The value wasn't saved above.
        self.assertNotIn("hello", request.session.load())