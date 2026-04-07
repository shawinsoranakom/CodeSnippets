async def async_view(request):
            return HttpResponse(headers={"Expires": "tomorrow"})