def form_view_with_template(request):
    "A view that tests a simple form"
    if request.method == "POST":
        form = TestForm(request.POST)
        if form.is_valid():
            message = "POST data OK"
        else:
            message = "POST data has errors"
    else:
        form = TestForm()
        message = "GET form page"
    return render(
        request,
        "form_view.html",
        {
            "form": form,
            "message": message,
        },
    )