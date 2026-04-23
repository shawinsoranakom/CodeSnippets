def test_httprequest_repr(self):
        request = HttpRequest()
        request.path = "/somepath/"
        request.method = "GET"
        request.GET = {"get-key": "get-value"}
        request.POST = {"post-key": "post-value"}
        request.COOKIES = {"post-key": "post-value"}
        request.META = {"post-key": "post-value"}
        self.assertEqual(repr(request), "<HttpRequest: GET '/somepath/'>")