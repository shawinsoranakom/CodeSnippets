def test_zero_quality(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/*;q=0,text/html"
        self.assertEqual(
            [str(accepted_type) for accepted_type in request.accepted_types],
            ["text/html"],
        )