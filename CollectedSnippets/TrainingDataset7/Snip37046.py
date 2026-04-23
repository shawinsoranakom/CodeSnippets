def test_unknown_mime_type(self):
        response = self.client.get("/%s/file.unknown" % self.prefix)
        self.assertEqual("application/octet-stream", response.headers["Content-Type"])
        response.close()