def log_non_default_args(args: Namespace | EngineArgs):
    from vllm.entrypoints.openai.cli_args import make_arg_parser

    non_default_args = {}

    # Handle Namespace
    if isinstance(args, Namespace):
        parser = make_arg_parser(FlexibleArgumentParser())
        for arg, default in vars(parser.parse_args([])).items():
            if default != getattr(args, arg):
                non_default_args[arg] = getattr(args, arg)

    # Handle EngineArgs instance
    elif isinstance(args, EngineArgs):
        default_args = EngineArgs(model=args.model)  # Create default instance
        for field in dataclasses.fields(args):
            current_val = getattr(args, field.name)
            default_val = getattr(default_args, field.name)
            if current_val != default_val:
                non_default_args[field.name] = current_val
        if default_args.model != EngineArgs.model:
            non_default_args["model"] = default_args.model
    else:
        raise TypeError(
            "Unsupported argument type. Must be Namespace or EngineArgs instance."
        )

    logger.info("non-default args: %s", non_default_args)