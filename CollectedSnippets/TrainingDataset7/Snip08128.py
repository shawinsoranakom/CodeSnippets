def get_response(self, request):
        try:
            return self.serve(request)
        except Http404 as e:
            return response_for_exception(request, e)