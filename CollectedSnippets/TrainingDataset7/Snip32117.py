def render_view_with_using(request):
    using = request.GET.get("using")
    return render(request, "shortcuts/using.html", using=using)