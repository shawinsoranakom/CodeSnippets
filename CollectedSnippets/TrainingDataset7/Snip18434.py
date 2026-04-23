def auth_processor_no_attr_access(request):
    render(request, "context_processors/auth_attrs_no_access.html")
    # *After* rendering, we check whether the session was accessed
    return render(
        request,
        "context_processors/auth_attrs_test_access.html",
        {"session_accessed": request.session.accessed},
    )