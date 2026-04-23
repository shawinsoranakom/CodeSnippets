def test_conditional_page_decorator_successful(self):
        @conditional_page
        def sync_view(request):
            response = HttpResponse()
            response.content = b"test"
            response["Cache-Control"] = "public"
            return response

        request = HttpRequest()
        request.method = "GET"
        response = sync_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.get("Etag"))