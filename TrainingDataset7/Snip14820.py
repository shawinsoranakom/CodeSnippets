def _make_csp_decorator(config_attr_name, config_attr_value):
    """General CSP override decorator factory."""

    if not isinstance(config_attr_value, dict):
        raise TypeError("CSP config should be a mapping.")

    def decorator(view_func):
        @wraps(view_func)
        async def _wrapped_async_view(request, *args, **kwargs):
            response = await view_func(request, *args, **kwargs)
            setattr(response, config_attr_name, config_attr_value)
            return response

        @wraps(view_func)
        def _wrapped_sync_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            setattr(response, config_attr_name, config_attr_value)
            return response

        if iscoroutinefunction(view_func):
            return _wrapped_async_view
        return _wrapped_sync_view

    return decorator