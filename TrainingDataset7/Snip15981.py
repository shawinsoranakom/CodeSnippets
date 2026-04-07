def redirect_to(modeladmin, request, selected):
    from django.http import HttpResponseRedirect

    return HttpResponseRedirect("/some-where-else/")