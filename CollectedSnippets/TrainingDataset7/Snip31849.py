def environ_view(request):
    return HttpResponse(
        "\n".join("%s: %r" % (k, v) for k, v in request.environ.items())
    )