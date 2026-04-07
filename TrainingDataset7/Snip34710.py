def _permission_protected_view(request):
    "A simple view that is permission protected."
    t = Template(
        "This is a permission protected test. "
        "Username is {{ user.username }}. "
        "Permissions are {{ user.get_all_permissions }}.",
        name="Permissions Template",
    )
    c = Context({"user": request.user})
    return HttpResponse(t.render(c))