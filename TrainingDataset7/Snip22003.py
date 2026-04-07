def file_upload_echo(request):
    """
    Simple view to echo back info about uploaded files for tests.
    """
    r = {k: f.name for k, f in request.FILES.items()}
    return JsonResponse(r)