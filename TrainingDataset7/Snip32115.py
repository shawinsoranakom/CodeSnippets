def render_view_with_content_type(request):
    return render(
        request,
        "shortcuts/render_test.html",
        {
            "foo": "FOO",
            "bar": "BAR",
        },
        content_type="application/x-rendertest",
    )