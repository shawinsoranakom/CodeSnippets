def no_template_used(request):
    template = Template("This is a string-based template")
    return HttpResponse(template.render(Context({})))