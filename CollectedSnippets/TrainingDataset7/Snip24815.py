def test_content_type_headers(self):
        r = HttpResponse("hello", headers={"Content-Type": "application/json"})
        self.assertEqual(r.headers["Content-Type"], "application/json")