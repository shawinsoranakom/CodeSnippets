def process_view(self, request, view_func, view_args, view_kwargs):
        log.append("processed view %s" % view_func.__name__)
        return None