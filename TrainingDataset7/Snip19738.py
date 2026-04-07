def test_both_headers(self):
        # See RFC 9110 Section 13.2.2.
        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/")
        self.assertNotModified(response)

        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/")
        self.assertNotModified(response)

        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_NONE_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/")
        self.assertFullResponse(response)

        self.client.defaults["HTTP_IF_MODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_NONE_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/")
        self.assertFullResponse(response)