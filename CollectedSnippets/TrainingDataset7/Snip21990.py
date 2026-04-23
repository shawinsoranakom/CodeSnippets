def handle_uncaught_exception(self, request, resolver, exc_info):
                ret = super().handle_uncaught_exception(request, resolver, exc_info)
                request.POST  # evaluate
                return ret