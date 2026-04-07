def process_template_response(self, request, response):
        response.context_data["mw"].append(self.__class__.__name__)
        return response