def process_response(self, request, response):
        rotate_token(request)
        return response