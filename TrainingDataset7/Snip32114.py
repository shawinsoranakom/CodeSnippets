def render_view_with_multiple_templates(request):
    return render(
        request,
        [
            "shortcuts/no_such_template.html",
            "shortcuts/render_test.html",
        ],
        {
            "foo": "FOO",
            "bar": "BAR",
        },
    )