def test_all_if_match(self):
        self.client.defaults["HTTP_IF_MATCH"] = "*"
        response = self.client.get("/condition/")
        self.assertFullResponse(response)
        response = self.client.get("/condition/no_etag/")
        self.assertEqual(response.status_code, 412)