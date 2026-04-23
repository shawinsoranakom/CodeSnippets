def test_no_compress_short_response(self):
        """
        Compression isn't performed on responses with short content.
        """
        self.resp.content = self.short_string
        r = GZipMiddleware(self.get_response)(self.req)
        self.assertEqual(r.content, self.short_string)
        self.assertIsNone(r.get("Content-Encoding"))