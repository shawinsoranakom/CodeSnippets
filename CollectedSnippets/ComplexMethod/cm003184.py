def set_recursively(hf_pointer, key, value, full_name, weight_type):
    for attribute in key.split("."):
        hf_pointer = getattr(hf_pointer, attribute)

    if weight_type is not None:
        hf_shape = getattr(hf_pointer, weight_type).shape
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
        hf_pointer.weight_g.data = value
    elif weight_type == "weight_v":
        hf_pointer.weight_v.data = value
    elif weight_type == "bias":
        hf_pointer.bias.data = value
    elif weight_type == "running_mean":
        hf_pointer.running_mean.data = value
    elif weight_type == "running_var":
        hf_pointer.running_var.data = value
    elif weight_type == "num_batches_tracked":
        hf_pointer.num_batches_tracked.data = value
    elif weight_type == "weight_ih_l0":
        hf_pointer.weight_ih_l0.data = value
    elif weight_type == "weight_hh_l0":
        hf_pointer.weight_hh_l0.data = value
    elif weight_type == "bias_ih_l0":
        hf_pointer.bias_ih_l0.data = value
    elif weight_type == "bias_hh_l0":
        hf_pointer.bias_hh_l0.data = value
    elif weight_type == "weight_ih_l1":
        hf_pointer.weight_ih_l1.data = value
    elif weight_type == "weight_hh_l1":
        hf_pointer.weight_hh_l1.data = value
    elif weight_type == "bias_ih_l1":
        hf_pointer.bias_ih_l1.data = value
    elif weight_type == "bias_hh_l1":
        hf_pointer.bias_hh_l1.data = value
    else:
        hf_pointer.data = value

    logger.info(f"{key + ('.' + weight_type if weight_type is not None else '')} was initialized from {full_name}.")