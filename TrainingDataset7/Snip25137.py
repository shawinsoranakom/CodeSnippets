def test_default_lang_fallback_without_prefix(self):
        response = self.client.get("/simple/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Yes")