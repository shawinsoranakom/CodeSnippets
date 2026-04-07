def process_response(self, request, response):
        # This should never receive unrendered content.
        request.process_response_content = response.content
        request.process_response_reached = True
        return response