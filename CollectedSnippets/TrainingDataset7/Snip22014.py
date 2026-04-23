def file_upload_traversal_view(request):
    request.upload_handlers.insert(0, TraversalUploadHandler())
    request.FILES  # Trigger file parsing.
    return JsonResponse(
        {"file_name": request.upload_handlers[0].file_name},
    )