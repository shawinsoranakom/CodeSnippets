def _chunk_dtensor(
    tensor: torch.Tensor,
    rank: int,
    device_mesh: DeviceMesh,
) -> DTensor:
    """
    Shard a tensor to chunks along the first dimension.

    The local rank will gets its corresponding chunk as the local tensor to create a DTensor.
    """
    root_mesh = device_mesh._get_root_mesh() if device_mesh is not None else None
    if root_mesh is None:
        raise RuntimeError("No parent device_mesh is found for FSDP device_mesh.")
    if root_mesh.ndim < 2:
        raise RuntimeError(
            f"Found parent device_mesh of ndim={root_mesh.ndim},",
            "but meshes must be at least 2D.",
        )

    # We need to explicitly call .detach() to return a new tensor detached from the current graph.
    tensor = tensor.detach().clone()

    # When a layer is not involved in TP, then the tensor will not be a DTensor.
    # e.g. When a layer is not sppecified in the parallelize_plan, TP will have no effect on the layer.
    # e.g. When you do PairwiseParallel on a 3 layer model, TP will have no effect on the third layer.
    if isinstance(tensor, torch.Tensor) and not isinstance(tensor, DTensor):
        # For tensors, it is replicated across tp dimension and sharded across FSDP dimension.
        # TP is the inner dimension and FSDP is the outer dimension.
        # Therefore, shard placements for tensor is (Shard(0), Replicate()).
        replicate_placements = [Replicate() for _ in range(root_mesh.ndim)]
        shard_placements = [Replicate() for _ in range(root_mesh.ndim)]
        shard_placements[0] = DShard(0)  # type: ignore[call-overload]

        return DTensor.from_local(
            tensor, root_mesh, replicate_placements, run_check=False
        ).redistribute(
            device_mesh=root_mesh,
            placements=shard_placements,
        )

    else:
        tp_placements = tensor.placements
        tp_placement = tp_placements[0]

        tensor = tensor.to_local()

        # For DTensors, it is sharded across tp dimension first and then sharded across FSDP dimension.
        # TP is the inner dimension and FSDP is the outer dimension.
        # Therefore, shard placements for tensor is (Shard(0), tp_placement).
        # For higher dimensional meshes, it is replicated across other dimensions. For example, with
        # HSDP the shard placements for tensor is (Replicate, Shard(0), tp_placement).
        replicate_placements = [Replicate() for _ in range(root_mesh.ndim)]
        replicate_placements[-1] = tp_placement  # type: ignore[call-overload]
        shard_placements = [Replicate() for i in range(root_mesh.ndim)]  # type: ignore[misc]
        shard_placements[-2] = DShard(0)  # type: ignore[call-overload]
        shard_placements[-1] = tp_placement  # type: ignore[call-overload]

        return DTensor.from_local(
            tensor, root_mesh, replicate_placements, run_check=False
        ).redistribute(
            device_mesh=root_mesh,
            placements=shard_placements,
        )