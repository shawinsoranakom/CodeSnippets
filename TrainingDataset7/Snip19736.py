def test_weak_if_match(self):
        """
        If-Match comparisons use strong matching, so any comparison involving
        a weak ETag return a 412 response.
        """
        self.client.defaults["HTTP_IF_MATCH"] = ETAG
        response = self.client.get("/condition/weak_etag/")
        self.assertEqual(response.status_code, 412)

        self.client.defaults["HTTP_IF_MATCH"] = WEAK_ETAG
        response = self.client.get("/condition/weak_etag/")
        self.assertEqual(response.status_code, 412)
        response = self.client.get("/condition/")
        self.assertEqual(response.status_code, 412)