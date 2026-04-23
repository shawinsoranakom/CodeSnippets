def test_kwargs(self):
        response = self._response(
            content_type="application/json", status=504, charset="ascii"
        )
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.charset, "ascii")