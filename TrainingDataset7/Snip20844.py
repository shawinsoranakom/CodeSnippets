async def stream_view(request):
            async def content():
                for _ in range(5):
                    yield self.content.encode()

            return StreamingHttpResponse(content())