def get(self, request, pk):
        return HttpResponse(f"Params: {pk}")