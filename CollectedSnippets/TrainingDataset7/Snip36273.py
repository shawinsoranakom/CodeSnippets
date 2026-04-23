def template_response_view(request):
            template = engines["django"].from_string("Hello world")
            return TemplateResponse(request, template)