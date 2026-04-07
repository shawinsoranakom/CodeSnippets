def file_upload_view_verify(request):
    """
    Use the sha digest hash to verify the uploaded contents.
    """
    form_data = request.POST.copy()
    form_data.update(request.FILES)

    for key, value in form_data.items():
        if key.endswith("_hash"):
            continue
        if key + "_hash" not in form_data:
            continue
        submitted_hash = form_data[key + "_hash"]
        if isinstance(value, UploadedFile):
            new_hash = hashlib.sha1(value.read()).hexdigest()
        else:
            new_hash = hashlib.sha1(value.encode()).hexdigest()
        if new_hash != submitted_hash:
            return HttpResponseServerError()

    # Adding large file to the database should succeed
    largefile = request.FILES["file_field2"]
    obj = FileModel()
    obj.testfile.save(largefile.name, largefile)

    return HttpResponse()