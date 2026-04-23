def auth_processor_messages(request):
    info(request, "Message 1")
    return render(request, "context_processors/auth_attrs_messages.html")