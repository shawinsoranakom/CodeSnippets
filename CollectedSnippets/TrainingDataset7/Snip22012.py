def file_upload_content_type_extra(request):
    """
    Simple view to echo back extra content-type parameters.
    """
    params = {}
    for file_name, uploadedfile in request.FILES.items():
        params[file_name] = {
            k: v.decode() for k, v in uploadedfile.content_type_extra.items()
        }
    return JsonResponse(params)