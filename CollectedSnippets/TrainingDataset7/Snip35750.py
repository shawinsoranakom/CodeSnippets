def process_response(self, *args, **kwargs):
        return HttpResponse(reverse("inner"))