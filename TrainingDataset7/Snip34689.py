def put_view(request):
    if request.method == "PUT":
        t = Template("Data received: {{ data }} is the body.", name="PUT Template")
        c = Context(
            {
                "Content-Length": request.META["CONTENT_LENGTH"],
                "data": request.body.decode(),
            }
        )
    else:
        t = Template("Viewing GET page.", name="Empty GET Template")
        c = Context()
    return HttpResponse(t.render(c))