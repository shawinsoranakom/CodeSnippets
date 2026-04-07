def subview_calling_view(request):
    with urlopen(request.GET["url"] + "/subview/") as response:
        return HttpResponse("subview calling view: {}".format(response.read().decode()))