def hello_meta(request):
    return HttpResponse(
        "From %s" % request.META.get("HTTP_REFERER") or "",
        content_type=request.META.get("CONTENT_TYPE"),
    )