def test_deepcopy(self):
        request = RequestFactory().get("/")
        request.session = {}
        request_copy = copy.deepcopy(request)
        request.session["key"] = "value"
        self.assertEqual(request_copy.session, {})