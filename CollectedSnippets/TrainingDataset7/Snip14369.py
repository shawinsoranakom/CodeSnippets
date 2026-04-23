def __call__(self, request):
        # Exit out to async mode, if needed
        if self.async_mode:
            return self.__acall__(request)
        response = None
        if hasattr(self, "process_request"):
            response = self.process_request(request)
        response = response or self.get_response(request)
        if hasattr(self, "process_response"):
            response = self.process_response(request, response)
        return response