def test_session_save_on_500(self):
        def response_500(request):
            response = HttpResponse("Horrible error")
            response.status_code = 500
            request.session["hello"] = "world"
            return response

        request = self.request_factory.get("/")
        SessionMiddleware(response_500)(request)

        # The value wasn't saved above.
        self.assertNotIn("hello", request.session.load())