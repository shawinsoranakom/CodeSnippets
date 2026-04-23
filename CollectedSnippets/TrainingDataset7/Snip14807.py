def _view_wrapper(request, *args, **kw):
                _check_request(request, "cache_control")
                response = viewfunc(request, *args, **kw)
                patch_cache_control(response, **kwargs)
                return response