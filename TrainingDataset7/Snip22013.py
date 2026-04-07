def file_upload_fd_closing(request, access):
    if access == "t":
        request.FILES  # Trigger file parsing.
    return HttpResponse()