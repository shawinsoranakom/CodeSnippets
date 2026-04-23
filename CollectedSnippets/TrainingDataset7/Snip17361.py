async def view(request):
            return StreamingHttpResponse(streaming_response())