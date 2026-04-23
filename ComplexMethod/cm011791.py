def maybe_copy_cpu_scalar(x: TensorBox, device: torch.device) -> TensorBox:
    """
    Copy cpu scalar if doesn't not match with given `device`
    """
    if not isinstance(x.data, ir.ReinterpretView) or has_free_unbacked_symbols(
        x.get_size()
    ):
        return x
    size = V.graph.sizevars.guarding_hints_or_throw(x.get_size())
    cur_device = x.get_device()
    if (
        cur_device is not None
        and cur_device.type == "cpu"
        and cur_device != device
        and (len(size) == 0 or (len(size) == 1 and size[0] == 1))
    ):
        return TensorBox(ir.StorageBox(ir.DeviceCopy.create(x, cur_device, False)))
    return x