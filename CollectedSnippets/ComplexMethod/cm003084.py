def set_recursively(hf_pointer, key, value, full_name, weight_type, is_finetuned):
    for attribute in key.split("."):
        if is_finetuned:
            if attribute in ["quantizer", "project_q", "project_hid"]:
                # those layers are only relevant for pretraining and should be dropped
                return

            if attribute == "ctc_proj":
                # we should rename `ctc_proj` to `lm_head` for fine-tuned phoneme models
                attribute = "lm_head"

        hf_pointer = getattr(hf_pointer, attribute)

    if weight_type is not None:
        hf_shape = getattr(hf_pointer, weight_type).shape
    else:
        hf_shape = hf_pointer.shape

    assert hf_shape == value.shape, (
        f"Shape of hf {key + '.' + weight_type if weight_type is not None else ''} is {hf_shape}, but should be"
        f" {value.shape} for {full_name}"
    )

    if weight_type == "weight":
        hf_pointer.weight.data = value
    elif weight_type == "weight_g":
        hf_pointer.weight_g.data = value
    elif weight_type == "weight_v":
        hf_pointer.weight_v.data = value
    elif weight_type == "bias":
        hf_pointer.bias.data = value
    else:
        hf_pointer.data = value

    logger.info(f"{key + '.' + weight_type if weight_type is not None else ''} was initialized from {full_name}.")