def render_view_with_status(request):
    return render(
        request,
        "shortcuts/render_test.html",
        {
            "foo": "FOO",
            "bar": "BAR",
        },
        status=403,
    )