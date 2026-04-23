def forward(  # type: ignore[override]
        ctx,  # pyre-ignore[2]: Parameter must be annotated.
        input: torch.Tensor,
        device_mesh: DeviceMesh,
        placements: tuple[Placement, ...],
        run_check: bool,
        shape: torch.Size | None = None,
        stride: tuple[int, ...] | None = None,
        grad_placements: tuple[Placement, ...] | None = None,
    ) -> "DTensor":
        ctx.forward_input_placements = placements
        ctx.forward_input_device_mesh = device_mesh
        ctx.grad_placements = grad_placements
        ctx.set_materialize_grads(False)

        if shape and stride:
            tensor_shape, tensor_stride = shape, stride
        elif not shape and not stride:
            # if it's not by default run_check, we assume user is certain that each
            # rank has the same tensor shape, and we just use that to calculate the
            # global shape
            global_shape, global_stride = compute_global_tensor_info(
                input, device_mesh, placements
            )
            tensor_shape, tensor_stride = torch.Size(global_shape), tuple(global_stride)
        else:
            raise RuntimeError(
                f"Found shape:{shape}, stride:{stride}.",
                "Please pass both shape and stride at the same time.",
            )

        if not device_mesh._is_current_rank_part_of_mesh():
            # if the global rank is not participating in the device mesh, we
            # simply set the local tensor to an empty tensor
            input = input.new_empty(0, requires_grad=input.requires_grad)
        elif run_check:
            # TODO: support uneven sharding when global shape/stride not passed, by
            # building the global TensorMeta during check_tensor_meta
            check_shape_stride = not shape and not stride
            check_tensor_meta(input, check_shape_stride=check_shape_stride)
            # TODO: See if we need to make this run_check logic
            # have a corresponding backward.
            for idx, placement in enumerate(placements):
                if placement.is_replicate():
                    # broadcast rank 0 tensor to all ranks
                    # only broadcast if run_check is True
                    input = input.contiguous()
                    mesh_broadcast(input, device_mesh, mesh_dim=idx)

        dist_spec = DTensorSpec(
            device_mesh,
            placements,
            tensor_meta=TensorMeta(
                tensor_shape,
                tensor_stride,
                input.dtype,
            ),
        )

        # We want a fresh Tensor object that shares memory with the input tensor
        # pyrefly: ignore [bad-argument-type]
        dist_tensor = DTensor(
            # pyrefly: ignore [bad-argument-count]
            input.view_as(input),
            dist_spec,
            # requires_grad of the dist tensor depends on if input
            # requires_grad or not
            # pyrefly: ignore [unexpected-keyword]
            requires_grad=input.requires_grad,
        )
        return dist_tensor