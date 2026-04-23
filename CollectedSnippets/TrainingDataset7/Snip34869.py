def return_text_file(request):
    "A view that parses and returns text as a file."
    match = CONTENT_TYPE_RE.match(request.META["CONTENT_TYPE"])
    if match:
        charset = match[1]
    else:
        charset = settings.DEFAULT_CHARSET

    return HttpResponse(
        request.body, status=200, content_type="text/plain; charset=%s" % charset
    )