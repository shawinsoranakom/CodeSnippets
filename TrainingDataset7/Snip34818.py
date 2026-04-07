def test_empty_string_data(self):
        """
        Request a view with empty string data via request method GET/POST/HEAD
        """
        # Regression test for #21740
        response = self.client.get("/body/", data="", content_type="application/json")
        self.assertEqual(response.content, b"")
        response = self.client.post("/body/", data="", content_type="application/json")
        self.assertEqual(response.content, b"")
        response = self.client.head("/body/", data="", content_type="application/json")
        self.assertEqual(response.content, b"")