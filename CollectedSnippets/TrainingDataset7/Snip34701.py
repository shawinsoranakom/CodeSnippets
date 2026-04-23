def redirect_to_different_hostname(request):
    return HttpResponseRedirect("https://hostname2/get_host_view/")