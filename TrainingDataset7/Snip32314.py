def setUp(self):
        request = HttpRequest()
        request.META = {"HTTP_HOST": "example.com"}
        self.site = RequestSite(request)