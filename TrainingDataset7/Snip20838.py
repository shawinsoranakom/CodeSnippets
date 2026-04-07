async def test_async_streaming_response_yields_chunks_incrementally(self):
        @gzip_page
        async def stream_view(request):
            async def content():
                for _ in range(5):
                    yield self.content.encode()

            return StreamingHttpResponse(content())

        request = HttpRequest()
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip"
        response = await stream_view(request)
        compressed_chunks = [chunk async for chunk in response]
        # Each input chunk should produce compressed output, not buffer
        # everything into a single chunk.
        self.assertGreater(len(compressed_chunks), 2)