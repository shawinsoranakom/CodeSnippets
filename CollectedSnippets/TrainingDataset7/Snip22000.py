def file_upload_view(request):
    """
    A file upload can be updated into the POST dictionary.
    """
    form_data = request.POST.copy()
    form_data.update(request.FILES)
    if isinstance(form_data.get("file_field"), UploadedFile) and isinstance(
        form_data["name"], str
    ):
        # If a file is posted, the dummy client should only post the file name,
        # not the full path.
        if os.path.dirname(form_data["file_field"].name) != "":
            return HttpResponseServerError()
        return HttpResponse()
    else:
        return HttpResponseServerError()