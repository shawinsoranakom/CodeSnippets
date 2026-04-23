def create(cls, x: IRNode, device: torch.device, non_blocking: bool) -> IRNode:
        x_device = x.get_device()
        assert x_device is not None
        if (
            not x.is_extern()
            # Can not apply this optimization if x has been mutated
            and try_get_name(x) not in V.graph.mutated_buffers
            and all(r in V.graph.constants for r in x.get_read_names())
            and not config.aot_inductor.use_runtime_constant_folding
        ):
            if V.graph.cpp_wrapper:
                # Even if x is promoted to be a device constant, we still need to
                # register device info to construct the correct CppWrapper class later
                V.graph.add_device_info(device)
                V.graph.add_device_info(x_device)
            return x.constant_to_device(device)

        V.graph.add_device_info(device)
        V.graph.add_device_info(x_device)
        developer_warning("DeviceCopy in input program")
        constant_args = (non_blocking,)
        # Device Copy should keep the same layout as input
        x = ExternKernel.require_contiguous(x)
        stride = None
        if x.get_size():
            # x.get_stride() may be unimplemented if x's size is empty
            stride = x.get_stride()
        is_destination_pinned = (
            is_gpu(x_device.type) and device.type == "cpu" and non_blocking
        )
        is_source_pinned = (
            x_device.type == "cpu" and is_gpu(device.type) and non_blocking
        )
        if is_source_pinned and is_storage_and_layout(x):
            x.get_layout().is_pinned = True
        return DeviceCopy(
            FixedLayout(
                device,
                x.get_dtype(),
                x.get_size(),
                stride,
                is_pinned=is_destination_pinned,
            ),
            [cls.realize_input(x)],
            constant_args,
        )