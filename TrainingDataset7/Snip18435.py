def auth_processor_attr_access(request):
    render(request, "context_processors/auth_attrs_access.html")
    return render(
        request,
        "context_processors/auth_attrs_test_access.html",
        {"session_accessed": request.session.accessed},
    )