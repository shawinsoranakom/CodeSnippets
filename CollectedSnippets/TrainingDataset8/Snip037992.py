def _get_command_telemetry(
    _command_func: Callable[..., Any], _command_name: str, *args, **kwargs
) -> Command:
    """Get telemetry information for the given callable and its arguments."""
    arg_keywords = inspect.getfullargspec(_command_func).args
    self_arg: Optional[Any] = None
    arguments: List[Argument] = []
    is_method = inspect.ismethod(_command_func)
    name = _command_name

    for i, arg in enumerate(args):
        pos = i
        if is_method:
            # If func is a method, ignore the first argument (self)
            i = i + 1

        keyword = arg_keywords[i] if len(arg_keywords) > i else f"{i}"
        if keyword == "self":
            self_arg = arg
            continue
        argument = Argument(k=keyword, t=_get_type_name(arg), p=pos)

        arg_metadata = _get_arg_metadata(arg)
        if arg_metadata:
            argument.m = arg_metadata
        arguments.append(argument)
    for kwarg, kwarg_value in kwargs.items():
        argument = Argument(k=kwarg, t=_get_type_name(kwarg_value))

        arg_metadata = _get_arg_metadata(kwarg_value)
        if arg_metadata:
            argument.m = arg_metadata
        arguments.append(argument)

    top_level_module = _get_top_level_module(_command_func)
    if top_level_module != "streamlit":
        # If the gather_metrics decorator is used outside of streamlit library
        # we enforce a prefix to be added to the tracked command:
        name = f"external:{top_level_module}:{name}"

    if (
        name == "create_instance"
        and self_arg
        and hasattr(self_arg, "name")
        and self_arg.name
    ):
        name = f"component:{self_arg.name}"

    return Command(name=name, args=arguments)