def process_exception(self, request, exception):
        return HttpResponse("Exception caught")