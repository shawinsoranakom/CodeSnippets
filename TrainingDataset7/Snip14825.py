def _wrapped_sync_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            setattr(response, config_attr_name, config_attr_value)
            return response