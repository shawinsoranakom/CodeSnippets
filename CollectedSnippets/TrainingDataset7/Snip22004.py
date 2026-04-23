def file_upload_echo_content(request):
    """
    Simple view to echo back the content of uploaded files for tests.
    """

    def read_and_close(f):
        with f:
            return f.read().decode()

    r = {k: read_and_close(f) for k, f in request.FILES.items()}
    return JsonResponse(r)