def _view_wrapper(request, *args, **kwargs):
            _check_request(request, "never_cache")
            response = view_func(request, *args, **kwargs)
            add_never_cache_headers(response)
            return response