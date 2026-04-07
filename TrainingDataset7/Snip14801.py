def cache_control(**kwargs):
    def _cache_controller(viewfunc):
        if iscoroutinefunction(viewfunc):

            async def _view_wrapper(request, *args, **kw):
                _check_request(request, "cache_control")
                response = await viewfunc(request, *args, **kw)
                patch_cache_control(response, **kwargs)
                return response

        else:

            def _view_wrapper(request, *args, **kw):
                _check_request(request, "cache_control")
                response = viewfunc(request, *args, **kw)
                patch_cache_control(response, **kwargs)
                return response

        return wraps(viewfunc)(_view_wrapper)

    return _cache_controller