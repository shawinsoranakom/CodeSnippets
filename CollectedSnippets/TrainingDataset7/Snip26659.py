def test_no_compress_incompressible_response(self):
        """
        Compression isn't performed on responses with incompressible content.
        """
        self.resp.content = self.incompressible_string
        r = GZipMiddleware(self.get_response)(self.req)
        self.assertEqual(r.content, self.incompressible_string)
        self.assertIsNone(r.get("Content-Encoding"))