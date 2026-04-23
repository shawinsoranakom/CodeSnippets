def test_newlines_in_headers(self):
        response = HttpResponse()
        with self.assertRaises(BadHeaderError):
            response["test\rstr"] = "test"
        with self.assertRaises(BadHeaderError):
            response["test\nstr"] = "test"