def test_require_http_methods_methods(self):
        @require_http_methods(["GET", "PUT"])
        def my_view(request):
            return HttpResponse("OK")

        request = HttpRequest()
        request.method = "GET"
        self.assertIsInstance(my_view(request), HttpResponse)
        request.method = "PUT"
        self.assertIsInstance(my_view(request), HttpResponse)
        request.method = "HEAD"
        self.assertIsInstance(my_view(request), HttpResponseNotAllowed)
        request.method = "POST"
        self.assertIsInstance(my_view(request), HttpResponseNotAllowed)
        request.method = "DELETE"
        self.assertIsInstance(my_view(request), HttpResponseNotAllowed)