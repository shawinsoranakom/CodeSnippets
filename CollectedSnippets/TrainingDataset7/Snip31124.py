def test_host_retrieval(self):
        request = HttpRequest()
        request.get_host = lambda: "www.example.com"
        request.path = ""
        self.assertEqual(
            request.build_absolute_uri(location="/path/with:colons"),
            "http://www.example.com/path/with:colons",
        )