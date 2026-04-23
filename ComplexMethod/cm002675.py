def __init__(self, *args, **kwargs: Any) -> None:
        # Extract only the fields that are part of the dataclass
        dataclass_fields = {f.name for f in fields(cls)}
        standard_kwargs = {k: v for k, v in kwargs.items() if k in dataclass_fields}

        # We need to call bare `__init__` without `__post_init__` but the `original_init` of
        # any dataclas contains a call to post-init at the end (without kwargs)
        if len(args) > 0:
            raise ValueError(
                f"{cls.__name__} accepts only keyword arguments, but found `{len(args)}` positional args."
            )

        for f in fields(cls):  # type: ignore
            if f.name in standard_kwargs:
                setattr(self, f.name, standard_kwargs[f.name])
            elif f.default is not MISSING:
                setattr(self, f.name, f.default)
            elif f.default_factory is not MISSING:
                setattr(self, f.name, f.default_factory())
            else:
                raise TypeError(f"Missing required field - '{f.name}'")

        # Pass any additional kwargs to `__post_init__` and let the object
        # decide whether to set the attr or use for different purposes (e.g. BC checks)
        additional_kwargs = {}
        for name, value in kwargs.items():
            if name not in dataclass_fields:
                additional_kwargs[name] = value

        self.__post_init__(**additional_kwargs)