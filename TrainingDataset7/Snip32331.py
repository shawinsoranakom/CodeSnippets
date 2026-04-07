def get_response(request):
            return HttpResponse(str(request.site.id))