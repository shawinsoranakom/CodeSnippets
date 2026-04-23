def a_view(request):
            return HttpResponse(headers={"Expires": "tomorrow"})