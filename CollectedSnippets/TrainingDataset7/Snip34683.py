async def async_generic_view(request):
            return HttpResponse(status=200, content=request.body)