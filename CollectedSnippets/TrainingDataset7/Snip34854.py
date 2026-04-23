def no_template_view(request):
    "A simple view that expects a GET request, and returns a rendered template"
    return HttpResponse(
        "No template used. Sample content: twice once twice. Content ends."
    )