def file_upload_quota(request):
    """
    Dynamically add in an upload handler.
    """
    request.upload_handlers.insert(0, QuotaUploadHandler())
    return file_upload_echo(request)