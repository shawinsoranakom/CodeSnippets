def file_upload_errors(request):
    request.upload_handlers.insert(0, ErroringUploadHandler())
    return file_upload_echo(request)