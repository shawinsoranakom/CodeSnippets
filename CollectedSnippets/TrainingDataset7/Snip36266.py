def process_template_response(self, request, response):
        request.process_template_response_reached = True
        return response