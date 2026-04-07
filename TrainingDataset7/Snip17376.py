async def streaming_view(request):
    sleep_time = float(request.GET["sleep"])
    return StreamingHttpResponse(streaming_inner(sleep_time))