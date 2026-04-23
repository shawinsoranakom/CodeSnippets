def get(self, request, *args, **kwargs):
        return HttpResponse("Hello (sync) world!")