def login_protected_view_changed_redirect(request):
    "A simple view that is login protected with a custom redirect field set"
    t = Template(
        "This is a login protected test. Username is {{ user.username }}.",
        name="Login Template",
    )
    c = Context({"user": request.user})
    return HttpResponse(t.render(c))