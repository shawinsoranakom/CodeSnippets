async def process_view(self, request, view_func, view_args, view_kwargs):
        return HttpResponse("Processed view %s" % view_func.__name__)