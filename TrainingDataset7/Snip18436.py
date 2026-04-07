def auth_processor_user(request):
    return render(request, "context_processors/auth_attrs_user.html")