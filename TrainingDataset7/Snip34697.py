def method_saving_308_redirect_query_string_view(request):
    return HttpResponseRedirect("/post_view/?hello=world", status=308)