def file_stop_upload_temporary_file(request):
    request.upload_handlers.insert(0, StopUploadTemporaryFileHandler())
    request.upload_handlers.pop(2)
    request.FILES  # Trigger file parsing.
    return JsonResponse(
        {"temp_path": request.upload_handlers[0].file.temporary_file_path()},
    )