def test_args(self):
        response = SimpleTemplateResponse("", {}, "application/json", 504)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.status_code, 504)