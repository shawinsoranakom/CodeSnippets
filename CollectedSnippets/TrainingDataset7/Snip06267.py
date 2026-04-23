def __call__(self, request):
        if self.is_async:
            return self.__acall__(request)
        self.process_request(request)
        return self.get_response(request)