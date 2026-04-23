def test_invalid_etag(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = '"""'
        response = self.client.get("/condition/etag/")
        self.assertFullResponse(response, check_last_modified=False)