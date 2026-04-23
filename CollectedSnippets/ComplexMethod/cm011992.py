def create(cls, inputs: Sequence[IRNode], dim: int) -> StorageBox:
        """
        Create the concat kernel from inputs
        """
        device = inputs[0].get_device()
        dtype = inputs[0].get_dtype()
        new_size = list(inputs[0].get_size())
        offsets_start = [0]
        offsets_end = [new_size[dim]]
        assert 0 <= dim < len(new_size)
        for i in range(1, len(inputs)):
            input_size = inputs[i].get_size()
            offsets_start.append(new_size[dim])
            assert len(input_size) == len(new_size)
            assert inputs[i].get_dtype() == dtype
            assert inputs[i].get_device() == device
            for j in range(len(new_size)):
                if j == dim:
                    new_size[j] = new_size[j] + input_size[j]
                else:
                    new_size[j] = V.graph.sizevars.check_equals_and_simplify(
                        new_size[j], input_size[j]
                    )
            offsets_end.append(new_size[dim])

        output_stride: Sequence[int] = FlexibleLayout.contiguous_strides(new_size)
        if config.comprehensive_padding:
            # Ensure the output stride matches the alignment requirements
            output_stride = Layout._pad_strides(
                output_stride, new_size, inputs[0].dtype
            )

        # If any of the inputs is in CL format, use CL format for the output
        for i in range(len(inputs)):
            x = inputs[i]
            if is_storage_and_layout(x):
                layout = x.get_layout()
                if isinstance(
                    layout, FixedLayout
                ) and Layout.is_channels_last_contiguous(layout.size, layout.stride):
                    # use CL stride for the output
                    output_stride = make_channels_last_strides_for(new_size)
                    break
        any_input_is_storage_and_layout = any(is_storage_and_layout(x) for x in inputs)
        fx_node_args = V.graph.current_node.args[0]
        # If any of the inputs has meta tensor and the meta tensor is in CL format, use CL format for the output
        # Skip this check when fx_node_args is not a list (e.g., called from _pad_as_cat).
        if (
            any_input_is_storage_and_layout is False
            and isinstance(fx_node_args, list)
            and any(
                # pyrefly: ignore [missing-attribute]
                "val" in arg.meta
                and (
                    # pyrefly: ignore [missing-attribute]
                    arg.meta["val"].is_contiguous(memory_format=torch.channels_last)
                    # pyrefly: ignore [missing-attribute]
                    or arg.meta["val"].is_contiguous(
                        memory_format=torch.channels_last_3d
                    )
                )
                for arg in fx_node_args
            )
        ):
            output_stride = make_channels_last_strides_for(new_size)

        is_pinned = all(
            is_storage_and_layout(x) and x.get_layout().is_pinned for x in inputs
        )

        assert device is not None
        concat_kernel = ConcatKernel(
            name=None,
            layout=FixedLayout(
                device=device,
                dtype=dtype,
                size=new_size,
                stride=output_stride,
                is_pinned=is_pinned,
            ),
            inputs=[],
        )
        kernel = StorageBox(concat_kernel)
        op_names = []
        for i, inp in enumerate(inputs):
            assert isinstance(inp, (BaseView, MutableBox)), type(inp)
            input_buffer = cls.realize_into(
                inp,
                SliceView.create(
                    kernel, dim, offsets_start[i], offsets_end[i], clamp=False
                ),
            )
            assert isinstance(input_buffer, Buffer), type(input_buffer)
            assert isinstance(concat_kernel.inputs, list), type(concat_kernel.inputs)
            concat_kernel.inputs.append(input_buffer)

            if isinstance(inp.data, BaseView):
                input_unwrapped = inp.data.unwrap_view()
            else:
                input_unwrapped = inp.data

            if (
                isinstance(input_unwrapped, StorageBox)
                and input_unwrapped.is_input_buffer()
                and (dev := inp.get_device()) is not None
                and is_gpu(dev.type)
                and not is_dynamic(input_buffer)
            ):
                op_names.append(input_buffer.get_operation_name())

        if len(op_names) > 1 and V.graph.has_feature(device, BackendFeature.FOREACH):
            V.graph.register_operation_list(op_names)

        concat_kernel.name = V.graph.register_buffer(concat_kernel)
        concat_kernel.inputs = cls.unwrap_storage(concat_kernel.inputs)
        V.graph.register_operation(concat_kernel)

        return kernel