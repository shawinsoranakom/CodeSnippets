def streaming_example_view(request):
    return StreamingHttpResponse((b"I", b"am", b"a", b"stream"))