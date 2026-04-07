def raises400_bad_request(request):
    raise BadRequest("Malformed request syntax")