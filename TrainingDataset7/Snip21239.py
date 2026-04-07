def process_response(self, request, response):
                response.thread_and_connection = request_lifecycle()
                return response