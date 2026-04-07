def auth_processor_perms(request):
    return render(request, "context_processors/auth_attrs_perms.html")