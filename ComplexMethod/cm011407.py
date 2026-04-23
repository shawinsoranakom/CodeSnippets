def _dtensor_init_helper(  # type: ignore[no-untyped-def]
    init_op,
    size: torch.Size,
    device_mesh: DeviceMesh | None = None,
    placements: Sequence[Placement] | None = None,
    **kwargs,
) -> DTensor:
    # if device_mesh is None, use the one from mesh resources
    device_mesh = device_mesh or _mesh_resources.get_current_mesh()
    kwargs["device"] = device_mesh.device_type

    # set default placements to replicated if not specified
    placements = placements or tuple(Replicate() for _ in range(device_mesh.ndim))

    # check device_mesh against placements
    if device_mesh.ndim != len(placements):
        raise AssertionError("mesh dimension does not match the length of placements")

    if kwargs["layout"] != torch.strided:
        raise AssertionError("layout value not supported!")
    torch_stride = torch._prims_common.make_contiguous_strides_for(size)

    # get local tensor shape
    local_shape, _ = compute_local_shape_and_global_offset(
        size, device_mesh, placements, skip_offset=True
    )

    # initialize the local tensor
    if init_op is torch.full:
        fill_value = kwargs.pop("fill_value", 0)
        local_tensor = init_op(local_shape, fill_value, **kwargs)
    elif init_op is torch.rand or init_op is torch.randn:
        # this tensor meta is not used except `shape`
        dtype = kwargs.get("dtype", torch.get_default_dtype())

        tensor_meta = TensorMeta(size, torch_stride, dtype)
        spec = DTensorSpec(device_mesh, tuple(placements), tensor_meta=tensor_meta)

        if random.is_rng_supported_mesh(device_mesh) and not random._rng_tracker:
            random._rng_tracker = random.OffsetBasedRNGTracker(device_mesh)

        if random._rng_tracker is None:
            raise AssertionError
        with random._rng_tracker._distribute_region(spec):
            local_tensor = init_op(local_shape, **kwargs)
    else:
        local_tensor = init_op(local_shape, **kwargs)

    spec = DTensorSpec(
        device_mesh,
        tuple(placements),
        tensor_meta=TensorMeta(
            size,
            torch_stride,
            local_tensor.dtype,
        ),
    )

    # pyrefly: ignore [bad-argument-type]
    return DTensor(
        # pyrefly: ignore [bad-argument-count]
        local_tensor,
        spec,
        # pyrefly: ignore [unexpected-keyword]
        requires_grad=kwargs["requires_grad"],
    )