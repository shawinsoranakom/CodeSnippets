def codegen_reinterpret_view(
        self,
        data,
        size,
        stride,
        offset,
        writeline: Callable[..., None],
        dtype=None,
    ) -> str:
        # Get the innermost buffer's layout info to help reinterpret view.
        # Consider a chain of (ReinterpretView <- TensorBox| StorageBox)... <- buffer
        # If we only use x.data to determine the reinterpret, we may get wrong layout.
        # For example:
        # x = ReinterpretView(
        #       Storage(
        #         ReinterpretView(
        #           storage(
        #             Buffer(name='buf0', layout=(size=(2, 5, 10), ...)
        #           ),
        #           layout=(10, 10),
        #         ),
        #       ),
        #       layout=(10, 10),
        #     )
        # In this case, x.data.layout == x.layout is (10, 10), the reinterpret view will return buf0,
        # but buf0 need to be viewed from (2, 5, 10) to (10, 10).
        # So we need to dig into the chain to find the innermost buffer's layout.
        d_size, d_stride, d_offset, d_dtype, collapsible = (
            codegen_reinterpret_view_helper(data)
        )

        def apply_reinterpret(
            name, tgt_size, tgt_stride, tgt_offset, cast_dtype, base_dtype
        ):
            s = self.codegen_python_shape_tuple(tgt_size)
            st = self.codegen_python_shape_tuple(tgt_stride)
            off = self.codegen_sizevar(tgt_offset)
            expr = f"reinterpret_tensor({name}, {s}, {st}, {off})"
            if cast_dtype is not None and cast_dtype != base_dtype:
                return f"aten.view.dtype({expr}, {cast_dtype})"
            return expr

        name = data.get_name()
        collapsed = collapsible and offset == d_offset
        if collapsed:
            same_layout = size == d_size and stride == d_stride
            base_dtype = d_dtype
        else:
            same_layout = (
                size == data.layout.size
                and stride == data.layout.stride
                and offset == data.layout.offset
            )
            base_dtype = data.dtype

        if same_layout:
            if dtype is not None and dtype != base_dtype:
                return f"aten.view.dtype({name}, {dtype})"
            return f"{name}"

        return apply_reinterpret(name, size, stride, offset, dtype, base_dtype)