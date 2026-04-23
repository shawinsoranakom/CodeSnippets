def test_gzip_page_decorator(self):
        @gzip_page
        def sync_view(request):
            return HttpResponse(content=self.content)

        request = HttpRequest()
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip"
        response = sync_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Encoding"), "gzip")