def assertFullResponse(self, response, check_last_modified=True, check_etag=True):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, FULL_RESPONSE.encode())
        if response.request["REQUEST_METHOD"] in ("GET", "HEAD"):
            if check_last_modified:
                self.assertEqual(response.headers["Last-Modified"], LAST_MODIFIED_STR)
            if check_etag:
                self.assertEqual(response.headers["ETag"], ETAG)
        else:
            self.assertNotIn("Last-Modified", response.headers)
            self.assertNotIn("ETag", response.headers)