def post_echo(request):
    if request.GET.get("echo"):
        return HttpResponse(request.body)
    else:
        return HttpResponse(status=204)