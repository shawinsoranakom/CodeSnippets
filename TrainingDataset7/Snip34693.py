def view_with_header(request):
    "A view that has a custom header"
    response = HttpResponse()
    response.headers["X-DJANGO-TEST"] = "Slartibartfast"
    return response