def collect_cuda_data_ptrs(obj: object) -> OrderedSet[int]:
    """Debug helper that collects the data pointers of all CUDA tensors in the object."""
    if not isinstance(obj, torch.Tensor):
        return OrderedSet()

    ptrs: OrderedSet[int] = OrderedSet()
    for base in get_plain_tensors(obj, out=[]):
        if type(base) is not torch.Tensor:
            continue
        if is_fake(base) or base.is_meta or base.device.type != "cuda":
            continue
        try:
            ptrs.add(base.data_ptr())
        except Exception:
            pass
    return ptrs