def find_expanded_modules(model: "PreTrainedModel", target_modules: list[str], num_layer_trainable: int) -> list[str]:
    r"""Find the modules in the expanded blocks to apply lora."""
    num_layers = getattr(model.config, "num_hidden_layers", None)
    if not num_layers:
        raise ValueError("Model was not supported.")

    if num_layers % num_layer_trainable != 0:
        raise ValueError(
            f"`num_layers` {num_layers} should be divisible by `num_layer_trainable` {num_layer_trainable}."
        )

    stride = num_layers // num_layer_trainable
    trainable_layer_ids = range(stride - 1, num_layers + stride - 1, stride)
    trainable_layers = [f".{idx:d}." for idx in trainable_layer_ids]
    module_names = []
    for name, _ in model.named_modules():
        if any(target_module in name for target_module in target_modules) and any(
            trainable_layer in name for trainable_layer in trainable_layers
        ):
            module_names.append(name)

    logger.info_rank0("Apply lora to layers: {}.".format(",".join(map(str, trainable_layer_ids))))
    return module_names