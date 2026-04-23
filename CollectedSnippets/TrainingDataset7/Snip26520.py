def add_template_response(request, message_type):
    for msg in request.POST.getlist("messages"):
        getattr(messages, message_type)(request, msg)
    return HttpResponseRedirect(reverse("show_template_response"))