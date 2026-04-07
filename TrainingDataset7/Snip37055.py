def test_index_custom_template(self):
        response = self.client.get("/%s/" % self.prefix)
        self.assertEqual(response.content, b"Test index")