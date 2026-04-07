def test_single_condition_1(self):
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_STR
        response = self.client.get("/condition/last_modified/")
        self.assertNotModified(response)
        response = self.client.get("/condition/etag/")
        self.assertFullResponse(response, check_last_modified=False)