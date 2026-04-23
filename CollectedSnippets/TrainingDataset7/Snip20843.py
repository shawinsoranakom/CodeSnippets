def stream_view(request):
            return StreamingHttpResponse(self.content.encode() for _ in range(5))