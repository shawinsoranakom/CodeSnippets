def _post_view_redirect(request, status_code):
    """Redirect to /post_view/ using the status code."""
    redirect_to = request.GET.get("to", "/post_view/")
    return HttpResponseRedirect(redirect_to, status=status_code)