def hello_cookie(request):
    response = HttpResponse("Hello World!")
    response.set_cookie("key", "value")
    return response