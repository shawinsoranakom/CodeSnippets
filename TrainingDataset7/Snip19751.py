def test_unquoted_if_none_match(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/unquoted_etag/")
        self.assertNotModified(response)
        response = self.client.put("/condition/unquoted_etag/")
        self.assertEqual(response.status_code, 412)
        self.client.defaults["HTTP_IF_NONE_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/unquoted_etag/")
        self.assertFullResponse(response, check_last_modified=False)