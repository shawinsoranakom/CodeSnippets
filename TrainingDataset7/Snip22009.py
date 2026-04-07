def file_upload_getlist_count(request):
    """
    Check the .getlist() function to ensure we receive the correct number of
    files.
    """
    file_counts = {}

    for key in request.FILES:
        file_counts[key] = len(request.FILES.getlist(key))
    return JsonResponse(file_counts)