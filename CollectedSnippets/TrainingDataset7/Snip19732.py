def test_if_none_match(self):
        self.client.defaults["HTTP_IF_NONE_MATCH"] = ETAG
        response = self.client.get("/condition/")
        self.assertNotModified(response)
        response = self.client.put("/condition/")
        self.assertEqual(response.status_code, 412)
        self.client.defaults["HTTP_IF_NONE_MATCH"] = EXPIRED_ETAG
        response = self.client.get("/condition/")
        self.assertFullResponse(response)

        # Several etags in If-None-Match is a bit exotic but why not?
        self.client.defaults["HTTP_IF_NONE_MATCH"] = "%s, %s" % (ETAG, EXPIRED_ETAG)
        response = self.client.get("/condition/")
        self.assertNotModified(response)