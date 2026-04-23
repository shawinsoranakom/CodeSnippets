def permission_protected_view(self, request):
        t = Template(
            "This is a permission protected test using a method. "
            "Username is {{ user.username }}. "
            "Permissions are {{ user.get_all_permissions }}.",
            name="Permissions Template",
        )
        c = Context({"user": request.user})
        return HttpResponse(t.render(c))