async def _wrapped_async_view(request, *args, **kwargs):
            response = await view_func(request, *args, **kwargs)
            setattr(response, config_attr_name, config_attr_value)
            return response