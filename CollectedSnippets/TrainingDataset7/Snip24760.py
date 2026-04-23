def streaming(request):
    return StreamingHttpResponse([b"streaming", b" ", b"content"])