def test_single_condition_4(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/etag/")
        self.assertFullResponse(response, check_last_modified=False)