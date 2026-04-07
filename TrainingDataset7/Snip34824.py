def test_json_wrong_header(self):
        response = self.client.get("/body/")
        msg = (
            'Content-Type header is "text/html; charset=utf-8", not "application/json"'
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.assertEqual(response.json(), {"key": "value"})