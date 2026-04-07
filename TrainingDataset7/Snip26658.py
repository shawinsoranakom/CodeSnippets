def test_no_compress_compressed_response(self):
        """
        Compression isn't performed on responses that are already compressed.
        """
        self.resp["Content-Encoding"] = "deflate"
        r = GZipMiddleware(self.get_response)(self.req)
        self.assertEqual(r.content, self.compressible_string)
        self.assertEqual(r.get("Content-Encoding"), "deflate")