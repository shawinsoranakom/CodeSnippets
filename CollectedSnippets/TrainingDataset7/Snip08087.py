def process_request(self, request):
        request.site = get_current_site(request)