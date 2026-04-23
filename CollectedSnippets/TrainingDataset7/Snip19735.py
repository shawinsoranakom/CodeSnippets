def test_if_match(self):
        self.client.defaults["HTTP_IF_MATCH"] = ETAG
        response = self.client.put("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_MATCH"] = EXPIRED_ETAG
        response = self.client.put("/condition/")
        self.assertEqual(response.status_code, 412)