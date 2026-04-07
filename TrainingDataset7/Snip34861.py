def redirect_to_self_with_changing_query_view(request):
    query = request.GET.copy()
    query["counter"] += "0"
    return HttpResponseRedirect(
        "/redirect_to_self_with_changing_query_view/?%s" % urlencode(query)
    )