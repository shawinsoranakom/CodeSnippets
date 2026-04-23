def __get_model_name(
    model_name,
    load_in_4bit = True,
    INT_TO_FLOAT_MAPPER = None,
    FLOAT_TO_INT_MAPPER = None,
    MAP_TO_UNSLOTH_16bit = None,
    load_in_fp8 = False,
    FLOAT_TO_FP8_BLOCK_MAPPER = None,
    FLOAT_TO_FP8_ROW_MAPPER = None,
):
    model_name = str(model_name)
    lower_model_name = model_name.lower()

    assert load_in_fp8 in (True, False, "block")
    if load_in_fp8 != False:
        if load_in_fp8 == True and (os.environ.get("UNSLOTH_HAS_FBGEMM", "0") == "1"):
            if lower_model_name in FLOAT_TO_FP8_ROW_MAPPER:
                # Faster row scaling only works if FBGEMM works!
                return FLOAT_TO_FP8_ROW_MAPPER[lower_model_name]
            elif lower_model_name in FLOAT_TO_FP8_BLOCK_MAPPER:
                # Otherwise we use the slower blockwise type
                return FLOAT_TO_FP8_BLOCK_MAPPER[lower_model_name]
        else:
            if lower_model_name in FLOAT_TO_FP8_BLOCK_MAPPER:
                return FLOAT_TO_FP8_BLOCK_MAPPER[lower_model_name]
        # Mapper didn't find a pre-quantized model.
        # For vllm >= 0.12.0, we can quantize the model to FP8 on the fly,
        # so just return the original model name. Older vllm versions will
        # fall through to offline quantization via _offline_quantize_to_fp8.
        if importlib.util.find_spec("vllm") is not None:
            import vllm

            if Version(vllm.__version__) >= Version("0.12.0"):
                return model_name
        return None

    elif not SUPPORTS_FOURBIT and lower_model_name in INT_TO_FLOAT_MAPPER:
        model_name = INT_TO_FLOAT_MAPPER[lower_model_name]
        print(
            f"Unsloth: Your transformers version of {transformers_version} does not support native "
            f"4bit loading.\nThe minimum required version is 4.37.\n"
            f'Try `pip install --upgrade "transformers>=4.37"`\n'
            f"to obtain the latest transformers build, then restart this session.\n"
            f"For now, we shall load `{model_name}` instead (still 4bit, just slower downloading)."
        )
        return model_name

    elif not load_in_4bit and lower_model_name in INT_TO_FLOAT_MAPPER:
        new_model_name = INT_TO_FLOAT_MAPPER[lower_model_name]
        # logger.warning_once(
        #     f"Unsloth: You passed in `{model_name}` which is a 4bit model, yet you set\n"\
        #     f"`load_in_4bit = False`. We shall load `{new_model_name}` instead."
        # )
        return new_model_name

    elif not load_in_4bit and lower_model_name in MAP_TO_UNSLOTH_16bit:
        new_model_name = MAP_TO_UNSLOTH_16bit[lower_model_name]
        return new_model_name

    elif load_in_4bit and SUPPORTS_FOURBIT and lower_model_name in FLOAT_TO_INT_MAPPER:
        # Support returning original full -bnb-4bit name if specified specifically
        # since we'll map it to the dynamic version instead
        if lower_model_name.endswith("-bnb-4bit"):
            return model_name

        new_model_name = FLOAT_TO_INT_MAPPER[lower_model_name]
        # logger.warning_once(
        #     f"Unsloth: You passed in `{model_name}` and `load_in_4bit = True`.\n"\
        #     f"We shall load `{new_model_name}` for 4x faster loading."
        # )
        return new_model_name

    return None