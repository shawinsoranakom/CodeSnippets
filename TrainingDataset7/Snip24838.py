async def test_async_streaming_response(self):
        async def async_iter():
            yield b"hello"
            yield b"world"

        r = StreamingHttpResponse(async_iter())

        chunks = []
        async for chunk in r:
            chunks.append(chunk)
        self.assertEqual(chunks, [b"hello", b"world"])