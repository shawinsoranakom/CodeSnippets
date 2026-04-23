def test_streaming_response_yields_chunks_incrementally(self):
        @gzip_page
        def stream_view(request):
            return StreamingHttpResponse(self.content.encode() for _ in range(5))

        request = HttpRequest()
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip"
        response = stream_view(request)
        compressed_chunks = list(response)
        # Each input chunk should produce compressed output, not buffer
        # everything into a single chunk.
        self.assertGreater(len(compressed_chunks), 2)