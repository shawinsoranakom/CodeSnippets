def get_model_param_count(model, trainable_only = False):
    """
    Calculate model's total param count. If trainable_only is True then count only those requiring grads
    """
    if is_deepspeed_zero3_enabled():

        def numel(p):
            return p.ds_numel if hasattr(p, "ds_numel") else p.numel()
    else:

        def numel(p):
            return p.numel()

    s = sum(
        numel(p) for p in model.parameters() if not trainable_only or p.requires_grad
    )
    if (
        (not trainable_only)
        and hasattr(model, "config")
        and hasattr(model.config, "quantization_config")
    ):
        approx = extract_quant_model_param_count(model)
        if approx is not None:
            s = approx
    return s