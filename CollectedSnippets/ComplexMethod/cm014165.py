def realize_all(
        cls,
        value: Any,
        cache: dict[int, tuple[Any, Any]] | None = None,
        *,
        allow_lazy_constant: bool = False,
    ) -> Any:
        """
        Walk an object and realize all LazyVariableTrackers inside it.
        """
        if cache is None:
            cache = {}

        idx = id(value)
        if idx in cache:
            return cache[idx][0]

        value_cls = type(value)
        if issubclass(value_cls, LazyVariableTracker):
            # Allow LazyConstantVariable to stay lazy when returning from a frame
            keep_lazy = allow_lazy_constant and isinstance(value, LazyConstantVariable)
            if keep_lazy:
                result = value
            else:
                result = cls.realize_all(
                    value.realize(), cache, allow_lazy_constant=allow_lazy_constant
                )
        elif issubclass(value_cls, VariableTracker):
            # update value in-place
            result = value
            # update cache now to prevent infinite recursion
            cache[idx] = (result, value)
            value_dict = value.__dict__
            nonvars = value._nonvar_fields
            for key in value_dict:
                if key not in nonvars:
                    value_dict[key] = cls.realize_all(
                        value_dict[key], cache, allow_lazy_constant=allow_lazy_constant
                    )
        elif value_cls is list:
            result = [
                cls.realize_all(v, cache, allow_lazy_constant=allow_lazy_constant)
                for v in value
            ]
        elif value_cls is tuple:
            result = tuple(
                cls.realize_all(v, cache, allow_lazy_constant=allow_lazy_constant)
                for v in value
            )
        elif value_cls in (dict, collections.OrderedDict):
            result = {
                k: cls.realize_all(v, cache, allow_lazy_constant=allow_lazy_constant)
                for k, v in list(value.items())
            }
        else:
            result = value

        # save `value` to keep it alive and ensure id() isn't reused
        cache[idx] = (result, value)
        return result