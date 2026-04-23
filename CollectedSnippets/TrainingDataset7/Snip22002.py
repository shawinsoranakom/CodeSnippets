def file_upload_unicode_name(request):
    # Check to see if Unicode name came through properly.
    if not request.FILES["file_unicode"].name.endswith(UNICODE_FILENAME):
        return HttpResponseServerError()
    # Check to make sure the exotic characters are preserved even
    # through file save.
    uni_named_file = request.FILES["file_unicode"]
    file_model = FileModel.objects.create(testfile=uni_named_file)
    full_name = f"{UPLOAD_FOLDER}/{uni_named_file.name}"
    return (
        HttpResponse()
        if file_model.testfile.storage.exists(full_name)
        else HttpResponseServerError()
    )