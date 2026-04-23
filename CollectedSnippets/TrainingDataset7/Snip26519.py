def add(request, message_type):
    # Don't default to False here to test that it defaults to False if
    # unspecified.
    fail_silently = request.POST.get("fail_silently", None)
    for msg in request.POST.getlist("messages"):
        if fail_silently is not None:
            getattr(messages, message_type)(request, msg, fail_silently=fail_silently)
        else:
            getattr(messages, message_type)(request, msg)
    return HttpResponseRedirect(reverse("show_message"))