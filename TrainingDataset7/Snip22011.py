def file_upload_filename_case_view(request):
    """
    Check adding the file to the database will preserve the filename case.
    """
    file = request.FILES["file_field"]
    obj = FileModel()
    obj.testfile.save(file.name, file)
    return HttpResponse("%s" % obj.pk)