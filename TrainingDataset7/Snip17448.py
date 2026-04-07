async def get(self, request, *args, **kwargs):
        return HttpResponse("Hello (async) world!")