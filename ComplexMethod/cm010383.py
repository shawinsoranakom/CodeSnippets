def write_single_view(prefix: str, tensor: Tensor, base_index: int):
        if f"{prefix}_base_index" in kwargs:
            raise AssertionError(f"{prefix}_base_index already in kwargs")
        if f"{prefix}_size" in kwargs:
            raise AssertionError(f"{prefix}_size already in kwargs")
        if f"{prefix}_stride" in kwargs:
            raise AssertionError(f"{prefix}_stride already in kwargs")
        if f"{prefix}_storage_offset" in kwargs:
            raise AssertionError(f"{prefix}_storage_offset already in kwargs")

        if f"{prefix}_slice_dim" in kwargs:
            raise AssertionError(f"{prefix}_slice_dim already in kwargs")
        if f"{prefix}_slice_start" in kwargs:
            raise AssertionError(f"{prefix}_slice_start already in kwargs")
        if f"{prefix}_slice_end" in kwargs:
            raise AssertionError(f"{prefix}_slice_end already in kwargs")

        def use_as_strided(tensor):
            kwargs[f"{prefix}_size"] = tensor.size()
            kwargs[f"{prefix}_stride"] = tensor.stride()
            kwargs[f"{prefix}_storage_offset"] = tensor.storage_offset()

        def use_slice(dim, start, end):
            kwargs[f"{prefix}_slice_dim"] = dim
            kwargs[f"{prefix}_slice_start"] = start
            kwargs[f"{prefix}_slice_end"] = end

        def use_alias():
            kwargs[f"{prefix}_alias"] = True

        # The start if the function
        if tensor is None:
            kwargs[f"{prefix}_base_index"] = None
        else:
            base = get_base(tensor)
            kwargs[f"{prefix}_base_index"] = base_index
            if base is None:
                # no need to add anything else other than _base_index
                return
            elif is_alias(base, tensor):
                use_alias()
            elif (slice_info := try_use_slice(base, tensor)) is not None:
                use_slice(*slice_info)
            else:
                use_as_strided(tensor)