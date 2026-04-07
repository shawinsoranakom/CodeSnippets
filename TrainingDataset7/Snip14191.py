def _precondition_failed(request):
    response = HttpResponse(status=412)
    log_response(
        "Precondition Failed: %s",
        request.path,
        response=response,
        request=request,
    )
    return response