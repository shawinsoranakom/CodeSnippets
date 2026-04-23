def test_all_if_none_match(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = "*"
        response = self.client.get("/condition/")
        self.assertNotModified(response)
        response = self.client.put("/condition/")
        self.assertEqual(response.status_code, 412)
        response = self.client.get("/condition/no_etag/")
        self.assertFullResponse(response, check_last_modified=False, check_etag=False)