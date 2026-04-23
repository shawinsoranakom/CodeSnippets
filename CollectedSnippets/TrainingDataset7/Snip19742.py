def test_single_condition_3(self):
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        response = self.client.get("/condition/last_modified/")
        self.assertFullResponse(response, check_etag=False)