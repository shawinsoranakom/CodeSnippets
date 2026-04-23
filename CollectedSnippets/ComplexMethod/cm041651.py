def get_args(args: InputArgument = None) -> tuple[ModelArguments, DataArguments, TrainingArguments, SampleArguments]:
    """Parse arguments from command line or config file."""
    parser = HfArgumentParser([ModelArguments, DataArguments, TrainingArguments, SampleArguments])
    allow_extra_keys = is_env_enabled("ALLOW_EXTRA_KEYS")

    if args is None:
        if len(sys.argv) > 1 and (sys.argv[1].endswith(".yaml") or sys.argv[1].endswith(".yml")):
            override_config = OmegaConf.from_cli(sys.argv[2:])
            dict_config = OmegaConf.load(Path(sys.argv[1]).absolute())
            args = OmegaConf.to_container(OmegaConf.merge(dict_config, override_config))
        elif len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
            override_config = OmegaConf.from_cli(sys.argv[2:])
            dict_config = OmegaConf.create(json.load(Path(sys.argv[1]).absolute()))
            args = OmegaConf.to_container(OmegaConf.merge(dict_config, override_config))
        else:  # list of strings
            args = sys.argv[1:]

    if isinstance(args, dict):
        (*parsed_args,) = parser.parse_dict(args, allow_extra_keys=allow_extra_keys)
    else:
        (*parsed_args, unknown_args) = parser.parse_args_into_dataclasses(args, return_remaining_strings=True)
        if unknown_args and not allow_extra_keys:
            print(parser.format_help())
            print(f"Got unknown args, potentially deprecated arguments: {unknown_args}")
            raise ValueError(f"Some specified arguments are not used by the HfArgumentParser: {unknown_args}")

    # Seed as early as possible after argument parsing so all downstream
    # components (dist init, dataloader, model init in run_* entrypoints) share the same RNG state.
    for arg in parsed_args:
        seed = getattr(arg, "seed", None)
        if seed is not None:
            set_seed(seed)
            break

    return tuple(parsed_args)