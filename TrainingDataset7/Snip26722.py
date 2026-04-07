def __call__(self, request):
        response = self.get_response(request)
        log.append((response.status_code, response.content))
        return response