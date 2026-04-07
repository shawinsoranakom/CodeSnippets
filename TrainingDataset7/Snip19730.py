def test_if_modified_since(self):
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_STR
        response = self.client.get("/condition/")
        self.assertNotModified(response)
        response = self.client.put("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_NEWER_STR
        response = self.client.get("/condition/")
        self.assertNotModified(response)
        response = self.client.put("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_INVALID_STR
        response = self.client.get("/condition/")
        self.assertFullResponse(response)
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        response = self.client.get("/condition/")
        self.assertFullResponse(response)