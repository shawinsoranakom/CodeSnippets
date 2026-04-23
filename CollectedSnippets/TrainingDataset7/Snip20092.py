def non_token_view_using_request_processor(request):
    """Use the csrf view processor instead of the token."""
    context = RequestContext(request, processors=[csrf])
    template = Template("")
    return HttpResponse(template.render(context))