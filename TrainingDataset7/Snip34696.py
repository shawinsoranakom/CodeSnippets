def method_saving_307_redirect_query_string_view(request):
    return HttpResponseRedirect("/post_view/?hello=world", status=307)