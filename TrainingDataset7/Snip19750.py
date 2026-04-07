def test_unquoted(self):
        """
        The same quoted ETag should be set on the header regardless of whether
        etag_func() in condition() returns a quoted or an unquoted ETag.
        """
        response_quoted = self.client.get("/condition/etag/")
        response_unquoted = self.client.get("/condition/unquoted_etag/")
        self.assertEqual(response_quoted["ETag"], response_unquoted["ETag"])