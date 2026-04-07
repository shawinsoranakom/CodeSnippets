def process_request(self, request):
        request._messages = default_storage(request)