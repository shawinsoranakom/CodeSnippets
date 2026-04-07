def test_random_bytes_streaming_response(self):
        """A random number of bytes is added to mitigate the BREACH attack."""

        def get_stream_response(request):
            resp = StreamingHttpResponse(self.sequence)
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp

        with mock.patch(
            "django.utils.text.secrets.randbelow", autospec=True, return_value=3
        ):
            r = GZipMiddleware(get_stream_response)(self.req)
            content = b"".join(r)
        # The fourth byte of a gzip stream contains flags.
        self.assertEqual(content[3], gzip.FNAME)
        # A 3 byte filename "aaa" and a null byte are added.
        self.assertEqual(content[10:14], b"aaa\x00")
        self.assertEqual(self.decompress(content), b"".join(self.sequence))