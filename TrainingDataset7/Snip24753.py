def template_response_error_handler(request, exception=None):
    return TemplateResponse(request, "test_handler.html", status=403)