def request_data(request, template="base.html", data="sausage"):
    "A simple view that returns the request data in the context"
    return render(
        request,
        template,
        {
            "get-foo": request.GET.get("foo"),
            "get-bar": request.GET.get("bar"),
            "post-foo": request.POST.get("foo"),
            "post-bar": request.POST.get("bar"),
            "data": data,
        },
    )