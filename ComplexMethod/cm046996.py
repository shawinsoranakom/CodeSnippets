def validate_loftq_config(loftq_config, lora_dropout, bias, init_lora_weights, model):
    from peft import LoraConfig

    if loftq_config is None:
        loftq_config = {}

    signature = str(inspect.signature(LoraConfig))
    SUPPORTS_LOFTQ = "loftq_config" in signature

    if lora_dropout != 0:
        logger.warning_once(
            f"Unsloth: Dropout = 0 is supported for fast patching. You are using dropout = {lora_dropout}.\n"
            f"Unsloth will patch all other layers, except LoRA matrices, causing a performance hit."
        )

    if bias != "none":
        logger.warning_once(
            f"Unsloth: bias = `none` is supported for fast patching. You are using bias = {bias}.\n"
            f"Unsloth will patch all other layers, except LoRA matrices, causing a performance hit."
        )

    if not (
        type(init_lora_weights) is bool
        or init_lora_weights == "gaussian"
        or init_lora_weights == "loftq"
        or init_lora_weights == "corda"
    ):
        raise ValueError(
            'Unsloth: `init_lora_weights` must be either [True, False, "gaussian", "loftq", "corda"].'
        )

    if init_lora_weights == "loftq":
        if not SUPPORTS_LOFTQ:
            import peft

            raise RuntimeError(
                f"Unsloth: Your PEFT version of {peft.__version__} does not support LoftQ init.\n"
                "Please install PEFT 0.7.2 or higher.\n"
                "You can also install from source: `pip install git+https://github.com/huggingface/peft.git"
            )

        if loftq_config == {}:
            from peft import LoftQConfig

            logger.warning_once(
                "Unsloth: init_lora_weights = `loftq` is set, but `loftq_config` is None.\n"
                "We shall use `loftq_config = LoftQConfig(loftq_bits = 4, loftq_iter = 1)`."
            )
            loftq_config = LoftQConfig(loftq_bits = 4, loftq_iter = 1)

        if hasattr(model.config, "quantization_config"):
            raise ValueError(
                "Unsloth: You are using `loftq` init, yet `load_in_4bit = True` was set.\n"
                "Reload your model without any quantization by setting `load_in_4bit = False`."
            )

    return loftq_config