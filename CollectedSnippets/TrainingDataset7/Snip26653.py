async def test_compress_async_streaming_response(self):
        """
        Compression is performed on responses with async streaming content.
        """

        async def get_stream_response(request):
            async def iterator():
                for chunk in self.sequence:
                    yield chunk

            resp = StreamingHttpResponse(iterator())
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp

        r = await GZipMiddleware(get_stream_response)(self.req)
        self.assertEqual(
            self.decompress(b"".join([chunk async for chunk in r])),
            b"".join(self.sequence),
        )
        self.assertEqual(r.get("Content-Encoding"), "gzip")
        self.assertFalse(r.has_header("Content-Length"))