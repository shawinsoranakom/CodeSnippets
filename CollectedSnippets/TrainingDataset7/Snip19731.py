def test_if_unmodified_since(self):
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = LAST_MODIFIED_STR
        response = self.client.get("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = LAST_MODIFIED_NEWER_STR
        response = self.client.get("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = LAST_MODIFIED_INVALID_STR
        response = self.client.get("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        response = self.client.get("/condition/")
        self.assertEqual(response.status_code, 412)