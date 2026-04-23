def show_template_response(request):
    template = engines["django"].from_string(TEMPLATE)
    return TemplateResponse(request, template)