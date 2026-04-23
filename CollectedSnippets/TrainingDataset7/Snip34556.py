def template_response_view(request):
    return TemplateResponse(request, "response.html", {})