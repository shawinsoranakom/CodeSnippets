def check_model_instance_from_subview(request):
    with urlopen(request.GET["url"] + "/create_model_instance/"):
        pass
    with urlopen(request.GET["url"] + "/model_view/") as response:
        return HttpResponse("subview calling view: {}".format(response.read().decode()))