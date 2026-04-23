def _view_wrapper(request, *args, **kwargs):
                response = func(request, *args, **kwargs)
                patch_vary_headers(response, headers)
                return response