def test_page_with_dash(self):
        # A page starting with /de* shouldn't match the 'de' language code.
        response = self.client.get("/de-simple-page-test/")
        self.assertEqual(response.content, b"Yes")