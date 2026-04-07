def test_async_streaming_response_warning(self):
        async def async_iter():
            yield b"hello"
            yield b"world"

        r = StreamingHttpResponse(async_iter())

        msg = (
            "StreamingHttpResponse must consume asynchronous iterators in order to "
            "serve them synchronously. Use a synchronous iterator instead."
        )
        with self.assertWarnsMessage(Warning, msg):
            self.assertEqual(list(r), [b"hello", b"world"])