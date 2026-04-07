def template_response(request):
    template = engines["django"].from_string(
        "template_response OK{% for m in mw %}\n{{ m }}{% endfor %}"
    )
    return TemplateResponse(request, template, context={"mw": []})