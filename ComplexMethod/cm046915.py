def get_model_name(
    model_name,
    load_in_4bit = True,
    load_in_fp8 = False,
    token = None,
    trust_remote_code = False,
):
    assert load_in_fp8 in (True, False, "block")
    new_model_name = _resolve_with_mappers(
        model_name = model_name,
        load_in_4bit = load_in_4bit,
        load_in_fp8 = load_in_fp8,
        int_to_float = INT_TO_FLOAT_MAPPER,
        float_to_int = FLOAT_TO_INT_MAPPER,
        map_to_unsloth_16bit = MAP_TO_UNSLOTH_16bit,
    )
    # In the rare case, we convert bad model names to other names
    # For eg too large dynamic quants or MoEs
    if (
        new_model_name is not None
        and type(new_model_name) is str
        and new_model_name.lower() in BAD_MAPPINGS
    ):
        new_model_name = BAD_MAPPINGS[new_model_name.lower()]

    if (
        new_model_name is None
        and model_name.count("/") == 1
        and model_name[0].isalnum()
    ):
        # Try checking if a new Unsloth version allows it!
        NEW_INT_TO_FLOAT_MAPPER, NEW_FLOAT_TO_INT_MAPPER, NEW_MAP_TO_UNSLOTH_16bit = (
            _get_new_mapper()
        )
        upgraded_model_name = _resolve_with_mappers(
            model_name = model_name,
            load_in_4bit = load_in_4bit,
            load_in_fp8 = load_in_fp8,
            int_to_float = NEW_INT_TO_FLOAT_MAPPER,
            float_to_int = NEW_FLOAT_TO_INT_MAPPER,
            map_to_unsloth_16bit = NEW_MAP_TO_UNSLOTH_16bit,
        )
        if upgraded_model_name is not None:
            raise NotImplementedError(
                f"Unsloth: {model_name} is not supported in your current Unsloth version! Please update Unsloth via:\n\n"
                "pip uninstall unsloth unsloth_zoo -y\n"
                'pip install --upgrade --no-cache-dir "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"\n'
                'pip install --upgrade --no-cache-dir "git+https://github.com/unslothai/unsloth-zoo.git"\n'
            )

    if new_model_name is None:
        new_model_name = model_name

    return new_model_name