def test_compress_streaming_response(self):
        """
        Compression is performed on responses with streaming content.
        """

        def get_stream_response(request):
            resp = StreamingHttpResponse(self.sequence)
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp

        r = GZipMiddleware(get_stream_response)(self.req)
        self.assertEqual(self.decompress(b"".join(r)), b"".join(self.sequence))
        self.assertEqual(r.get("Content-Encoding"), "gzip")
        self.assertFalse(r.has_header("Content-Length"))