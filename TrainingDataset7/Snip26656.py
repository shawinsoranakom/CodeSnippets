def test_compress_non_200_response(self):
        """
        Compression is performed on responses with a status other than 200
        (#10762).
        """
        self.resp.status_code = 404
        r = GZipMiddleware(self.get_response)(self.req)
        self.assertEqual(self.decompress(r.content), self.compressible_string)
        self.assertEqual(r.get("Content-Encoding"), "gzip")