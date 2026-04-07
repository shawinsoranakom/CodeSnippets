def decorator(func):
        if iscoroutinefunction(func):

            async def _view_wrapper(request, *args, **kwargs):
                response = await func(request, *args, **kwargs)
                patch_vary_headers(response, headers)
                return response

        else:

            def _view_wrapper(request, *args, **kwargs):
                response = func(request, *args, **kwargs)
                patch_vary_headers(response, headers)
                return response

        return wraps(func)(_view_wrapper)