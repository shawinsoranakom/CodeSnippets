def session_view(request):
    "A view that modifies the session"
    request.session["tobacconist"] = "hovercraft"

    t = Template(
        "This is a view that modifies the session.",
        name="Session Modifying View Template",
    )
    c = Context()
    return HttpResponse(t.render(c))