def render_view(request):
    return render(
        request,
        "shortcuts/render_test.html",
        {
            "foo": "FOO",
            "bar": "BAR",
        },
    )