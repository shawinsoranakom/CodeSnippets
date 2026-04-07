def get(self, request, *args, **kwargs):
        return HttpResponse(f"Hello {self.kwargs['name']}")