async def test_sync_streaming_response_warning(self):
        r = StreamingHttpResponse(iter(["hello", "world"]))

        msg = (
            "StreamingHttpResponse must consume synchronous iterators in order to "
            "serve them asynchronously. Use an asynchronous iterator instead."
        )
        with self.assertWarnsMessage(Warning, msg):
            self.assertEqual(b"hello", await anext(aiter(r)))