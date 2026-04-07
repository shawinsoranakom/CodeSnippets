def test_compress_streaming_response_unicode(self):
        """
        Compression is performed on responses with streaming Unicode content.
        """

        def get_stream_response_unicode(request):
            resp = StreamingHttpResponse(self.sequence_unicode)
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp

        r = GZipMiddleware(get_stream_response_unicode)(self.req)
        self.assertEqual(
            self.decompress(b"".join(r)),
            b"".join(x.encode() for x in self.sequence_unicode),
        )
        self.assertEqual(r.get("Content-Encoding"), "gzip")
        self.assertFalse(r.has_header("Content-Length"))