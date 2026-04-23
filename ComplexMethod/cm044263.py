def merge_args_and_kwargs(
        cls,
        func: Callable,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge args and kwargs into a single dict."""
        args = deepcopy(args)
        kwargs_copy = deepcopy(kwargs)
        parameter_list = cls.get_polished_parameter_list(func=func)
        parameter_map = {}

        for index, parameter in enumerate(parameter_list):
            if index < len(args):
                parameter_map[parameter.name] = args[index]
            elif parameter.name in kwargs:
                parameter_map[parameter.name] = kwargs[parameter.name]
            elif parameter.default is not parameter.empty:
                parameter_map[parameter.name] = parameter.default
            else:
                parameter_map[parameter.name] = None

        if "kwargs" in parameter_map:
            merged_kwargs = parameter_map.get("kwargs") or {}
            if not isinstance(merged_kwargs, dict):
                merged_kwargs = dict(merged_kwargs)

            for key, value in kwargs_copy.items():
                if key in {"filter_query", "kwargs"} or key in parameter_map:
                    continue
                merged_kwargs[key] = value

            parameter_map.update(merged_kwargs)
            parameter_map.pop("kwargs", None)

        return parameter_map