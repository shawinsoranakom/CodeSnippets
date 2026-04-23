def dot_product_attention(
    query,
    key,
    value,
    bias=None,
    mask=None,
    scale=None,
    is_causal=False,
    flash_attention=None,
    attn_logits_soft_cap=None,
):
    if bias is not None:
        raise NotImplementedError(
            "`dot_product_attention` with `bias` is not supported "
            "with openvino backend"
        )
    if flash_attention:
        raise NotImplementedError(
            "`dot_product_attention` with `flash_attention` is not supported "
            "with openvino backend"
        )
    if attn_logits_soft_cap is not None:
        raise NotImplementedError(
            "`dot_product_attention` with `attn_logits_soft_cap` is not "
            "supported with openvino backend"
        )
    query = get_ov_output(query)
    key = get_ov_output(key)
    value = get_ov_output(value)
    if query.get_element_type() != key.get_element_type():
        ov_type = OPENVINO_DTYPES[backend.floatx()]
        query = ov_opset.convert(query, ov_type).output(0)
        key = ov_opset.convert(key, ov_type).output(0)
    if value.get_element_type() != query.get_element_type():
        value = ov_opset.convert(value, query.get_element_type()).output(0)
    axes_const = ov_opset.constant([0, 2, 1, 3], Type.i32).output(0)

    query = ov_opset.transpose(query, axes_const)
    key = ov_opset.transpose(key, axes_const)
    value = ov_opset.transpose(value, axes_const)
    mask = get_ov_output(mask) if mask is not None else None
    scale = (
        get_ov_output(scale, query.get_element_type())
        if scale is not None
        else None
    )
    dpa = ov_opset.scaled_dot_product_attention(
        query, key, value, attention_mask=mask, scale=scale, causal=is_causal
    )
    dpa = ov_opset.transpose(dpa, axes_const)
    return OpenVINOKerasTensor(dpa.output(0))