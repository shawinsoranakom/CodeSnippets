def process_view(self, request, view_func, view_args, view_kwargs):
        request.process_view_reached = True