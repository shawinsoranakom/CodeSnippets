def test_single_condition_6(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/etag2/")
        self.assertNotModified(response)
        response = self.client.get("/condition/last_modified2/")
        self.assertFullResponse(response, check_etag=False)