def test_absolute_url(self):
        request = HttpRequest()
        url = "https://www.example.com/asdf"
        self.assertEqual(request.build_absolute_uri(location=url), url)