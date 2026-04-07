def __call__(self, request):
        response = self.get_response(request)
        response.status_code = 402
        return response