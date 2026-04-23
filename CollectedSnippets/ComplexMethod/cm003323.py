def set_recursively(key, value, full_name, weight_type, hf_pointer):
    for attribute in key.split("."):
        hf_pointer = getattr(hf_pointer, attribute)

    hf_param_name = None
    for param_key in PARAM_MAPPING:
        if full_name.endswith(param_key):
            hf_param_name = PARAM_MAPPING[full_name.split(".")[-1]]
            weight_type = "param"

    # fairseq uses nn.utils.weight_norm() while transformers switches to nn.utils.parametrizations.weight_norm()
    # the mapping between two versions:
    # https://github.com/pytorch/pytorch/blob/56935684c3dfad7841c83c719eeebecb560fe466/torch/nn/utils/parametrizations.py#L389-L395

    if weight_type is not None and weight_type != "param":
        if weight_type == "weight_g" and not hasattr(hf_pointer, "weight_g"):
            hf_shape = hf_pointer.parametrizations.weight.original0.shape
        elif weight_type == "weight_v" and not hasattr(hf_pointer, "weight_v"):
            hf_shape = hf_pointer.parametrizations.weight.original1.shape
        else:
            hf_shape = getattr(hf_pointer, weight_type).shape
    elif weight_type is not None and weight_type == "param":
        shape_pointer = hf_pointer
        for attribute in hf_param_name.split("."):
            shape_pointer = getattr(shape_pointer, attribute)
        hf_shape = shape_pointer.shape

        # let's reduce dimension
        value = value[0]
    else:
        hf_shape = hf_pointer.shape

    if hf_shape != value.shape:
        raise ValueError(
            f"Shape of hf {key + '.' + weight_type if weight_type is not None else ''} is {hf_shape}, but should be"
            f" {value.shape} for {full_name}"
        )

    if weight_type == "weight":
        hf_pointer.weight.data = value
    elif weight_type == "weight_g":
        if hasattr(hf_pointer, "weight_g"):
            hf_pointer.weight_g.data = value
        else:
            hf_pointer.parametrizations.weight.original0.data = value
    elif weight_type == "weight_v":
        if hasattr(hf_pointer, "weight_v"):
            hf_pointer.weight_v.data = value
        else:
            hf_pointer.parametrizations.weight.original1.data = value
    elif weight_type == "bias":
        hf_pointer.bias.data = value
    elif weight_type == "param":
        for attribute in hf_param_name.split("."):
            hf_pointer = getattr(hf_pointer, attribute)
        hf_pointer.data = value
    else:
        hf_pointer.data = value

    logger.info(f"{key + '.' + weight_type if weight_type is not None else ''} was initialized from {full_name}.")