def test_compress_response(self):
        """
        Compression is performed on responses with compressible content.
        """
        r = GZipMiddleware(self.get_response)(self.req)
        self.assertEqual(self.decompress(r.content), self.compressible_string)
        self.assertEqual(r.get("Content-Encoding"), "gzip")
        self.assertEqual(r.get("Content-Length"), str(len(r.content)))