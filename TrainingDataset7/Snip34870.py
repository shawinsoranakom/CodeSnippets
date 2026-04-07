def check_headers(request):
    "A view that responds with value of the X-ARG-CHECK header"
    return HttpResponse(
        "HTTP_X_ARG_CHECK: %s" % request.META.get("HTTP_X_ARG_CHECK", "Undefined")
    )