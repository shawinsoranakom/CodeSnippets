def test_content_type(self):
        r = HttpResponse("hello", content_type="application/json")
        self.assertEqual(r.headers["Content-Type"], "application/json")