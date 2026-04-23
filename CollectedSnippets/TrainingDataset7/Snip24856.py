def test_headers(self):
        response = HttpResponse()
        response["X-Foo"] = "bar"
        self.assertEqual(response["X-Foo"], "bar")
        self.assertEqual(response.headers["X-Foo"], "bar")
        self.assertIn("X-Foo", response)
        self.assertIs(response.has_header("X-Foo"), True)
        del response["X-Foo"]
        self.assertNotIn("X-Foo", response)
        self.assertNotIn("X-Foo", response.headers)
        # del doesn't raise a KeyError on nonexistent headers.
        del response["X-Foo"]