def __init_subclass__(cls, **kwargs):
                super().__init_subclass__()
                saved_kwargs.update(kwargs)