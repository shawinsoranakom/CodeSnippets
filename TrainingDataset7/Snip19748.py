def test_single_condition_9(self):
        self.client.defaults["HTTP_IF_UNMODIFIED_SINCE"] = EXPIRED_LAST_MODIFIED_STR
        response = self.client.get("/condition/last_modified2/")
        self.assertEqual(response.status_code, 412)
        response = self.client.get("/condition/etag2/")
        self.assertEqual(response.status_code, 412)