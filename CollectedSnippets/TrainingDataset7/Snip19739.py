def test_both_headers_2(self):
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_MATCH"] = ETAG
        response = self.client.get("/condition/")
        self.assertFullResponse(response)

        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_MATCH"] = ETAG
        response = self.client.get("/condition/")
        self.assertFullResponse(response)

        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/")
        self.assertEqual(response.status_code, 412)

        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = LAST_MODIFIED_STR
        self.client.defaults["HTTP_IF_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/")
        self.assertEqual(response.status_code, 412)