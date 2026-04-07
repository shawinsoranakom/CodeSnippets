def test_single_condition_2(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/etag/")
        self.assertNotModified(response)
        response = self.client.get("/condition/last_modified/")
        self.assertFullResponse(response, check_etag=False)