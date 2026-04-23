def interpret_gathered_like(tensors, gathered):
    offset = 0
    dest_views = []

    if gathered.dim() != 1 or gathered.element_size() != 1:
        raise ValueError(f"Buffer must be 1D and single-byte (got {gathered.dim()}D {gathered.dtype})")

    for tensor in tensors:

        if tensor is None:
            dest_views.append(None)
            continue

        if isinstance(tensor, QuantizedTensor):
            inner_tensors, qt_ctx = tensor.__tensor_flatten__()
            templates = { attr: getattr(tensor, attr) for attr in inner_tensors }
        else:
            templates = { "data": tensor }

        actuals = {}
        for attr, template in templates.items():
            size = template.numel() * template.element_size()
            if offset + size > gathered.numel():
                raise ValueError(f"Buffer too small: needs {offset + size} bytes, but only has {gathered.numel()}. ")
            actuals[attr] = gathered[offset:offset+size].view(dtype=template.dtype).view(template.shape)
            offset += vram_aligned_size(template)

        if isinstance(tensor, QuantizedTensor):
            dest_views.append(QuantizedTensor.__tensor_unflatten__(actuals, qt_ctx, 0, 0))
        else:
            dest_views.append(actuals["data"])

    return dest_views