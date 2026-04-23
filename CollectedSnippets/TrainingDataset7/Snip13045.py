def _accept(self, request):
        # Avoid checking the request twice by adding a custom attribute to
        # request. This will be relevant when both decorator and middleware
        # are used.
        request.csrf_processing_done = True
        return None