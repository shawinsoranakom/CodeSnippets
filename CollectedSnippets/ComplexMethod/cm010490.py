def try_convert_fake_to_real(
    ten_list: list[FakeTensor | Any],
) -> list[FakeTensor | torch.Tensor | Any]:
    """
    Attempt to convert fake tensors to a corresponding real tensor with the correct underlying storage by looking up
    the FakeTensorMode meta to real storage mapping. On failure to find the storage mapping, the FakeTensor will
    remain in the list.

    Note: this is not currently optimized (makes copies of the meta converter internal dictionaries)
    """

    fake_tensor = next(
        (item for item in ten_list if isinstance(item, FakeTensor)), None
    )
    if fake_tensor is None:
        return ten_list

    fake_mode = fake_tensor.fake_mode
    meta_converter = fake_mode.fake_tensor_converter.meta_converter
    desc = meta_converter.describer

    storage_to_key = {v: k for k, v in meta_converter.storage_memo.items()}
    key_to_real_storage = {v: k for k, v in desc.lookup_storage.items()}
    out = []
    for t in ten_list:
        if not isinstance(t, FakeTensor) or t.layout != torch.strided:
            out.append(t)
            continue

        key = storage_to_key.get(t.untyped_storage())
        real_storage = None if key is None else key_to_real_storage.get(key)
        if real_storage is None:
            out.append(t)
            continue

        unhinted = False

        def map_symint(s: torch.SymInt | int) -> int:
            nonlocal unhinted
            if not isinstance(s, torch.SymInt):
                return s
            unhinted = unhinted if not unhinted else s.node.has_hint()
            return s.node.hint

        stor_offset = map_symint(t.storage_offset())
        size = [map_symint(s) for s in t.shape]
        stride = [map_symint(s) for s in t.stride()]

        if unhinted:
            out.append(t)
            continue

        new_tensor = torch.empty(
            [],
            dtype=t.dtype,
            device=t.device,
        )
        new_tensor.set_(
            real_storage,
            storage_offset=stor_offset,
            size=size,
            stride=stride,
        )
        out.append(new_tensor.clone())

    return out