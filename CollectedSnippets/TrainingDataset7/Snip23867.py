def get_context_data(self, **kwargs):
        context = {"custom_key": "custom_value"}
        context.update(kwargs)
        return super().get_context_data(**context)