def __init__(self, to, on_delete, from_fields, to_fields, **kwargs):
        # Disable reverse relation
        kwargs["related_name"] = "+"
        # Set unique to enable model cache.
        kwargs["unique"] = True
        super().__init__(to, on_delete, from_fields, to_fields, **kwargs)