def restore_layer_on_meta(layer: torch.nn.Module, info: LayerReloadingInfo):
    """Restore a layer to model format with tensors on the meta device"""
    if layer.__class__.__name__ in SKIP_MODULES:
        return

    for name in get_layer_tensors(layer):
        if name not in SKIP_TENSORS:
            delattr(layer, name)

    restore_params, restore_buffers = info.restore_metadata
    for name, param in restore_params.items():
        if name not in SKIP_TENSORS:
            param = restore_layer_refs(param, layer)
            layer.register_parameter(name, param)

    for name, buffer in restore_buffers.items():
        if name not in SKIP_TENSORS:
            buffer = restore_layer_refs(buffer, layer)
            layer.register_buffer(name, buffer)