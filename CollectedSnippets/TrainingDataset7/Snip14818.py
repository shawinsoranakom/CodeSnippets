async def _view_wrapper(request, *args, **kwargs):
            return await view_func(request, *args, **kwargs)