def append_item(i: int, arg: Any) -> None:
        if Dim.check_exact(arg):
            d = arg
            if d._size == -1:
                d.size = sz[i]
            add_dim(d)
            append_size(i)
            append_flat_handle(arg)
            return

        info = TensorInfo.create(arg, False, False)
        if info:
            append_size(i)
            append_tensor_input(info)
            for level in info.levels:
                if not level.is_positional():
                    add_dim(level.dim())
            return

        if has_dimpacks_or_none:
            if isinstance(arg, (tuple, list)) and all(Dim.check_exact(d) for d in arg):
                # dim pack
                dim_pack = list(arg)
                for d in dim_pack:
                    add_dim(d)
                    append_flat_handle(d)
                _bind_dims_to_size(sz[i], sd[i], dim_pack, nsz, nsd)
                return

        append_size(i)
        append_flat_handle(arg)