def login_protected_view(request):
    "A simple view that is login protected."
    t = Template(
        "This is a login protected test. Username is {{ user.username }}.",
        name="Login Template",
    )
    c = Context({"user": request.user})

    return HttpResponse(t.render(c))