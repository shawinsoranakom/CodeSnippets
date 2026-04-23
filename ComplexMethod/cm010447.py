def tensor_attr_supported_getter(func, *args, **kwargs):
    if func is torch.ops.aten.is_non_overlapping_and_dense.default:
        return False

    if func is torch.ops.aten.sym_size.default:
        return args[0]._size

    if func is torch.ops.aten.dim.default:
        return len(args[0]._size)

    if func in (torch.ops.aten.sym_numel.default, torch.ops.aten.numel.default):
        if args[0]._lengths is not None:
            return int(sum(args[0]._lengths) * math.prod(args[0]._size[2:]))
        return args[0]._values.numel()

    if func is torch.ops.aten.sym_stride.default:
        return args[0]._strides

    if func is torch.ops.aten.sym_storage_offset.default:
        return args[0]._values.storage_offset()