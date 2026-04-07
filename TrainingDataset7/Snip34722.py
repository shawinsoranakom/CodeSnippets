def login_protected_view(self, request):
        t = Template(
            "This is a login protected test using a method. "
            "Username is {{ user.username }}.",
            name="Login Method Template",
        )
        c = Context({"user": request.user})
        return HttpResponse(t.render(c))