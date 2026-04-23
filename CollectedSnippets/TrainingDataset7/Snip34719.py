def upload_view(request):
    """Prints keys of request.FILES to the response."""
    return HttpResponse(", ".join(request.FILES))