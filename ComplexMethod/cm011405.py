def distribute_tensor(
    tensor: torch.Tensor,
    device_mesh: DeviceMesh | None = None,
    placements: Sequence[Placement] | None = None,
    *,
    src_data_rank: int | None = 0,
) -> DTensor:
    """
    Distribute a leaf ``torch.Tensor`` (i.e. nn.Parameter/buffers) to the ``device_mesh`` according
    to the ``placements`` specified. The rank of ``device_mesh`` and ``placements`` must be the
    same. The ``tensor`` to distribute is the logical or "global" tensor, and the API would use
    the ``tensor`` from first rank of the DeviceMesh dimension as the source of truth to preserve
    the single-device semantic. If you want to construct a DTensor in the middle of the Autograd
    computation, please use :meth:`DTensor.from_local` instead.

    Args:
        tensor (torch.Tensor): torch.Tensor to be distributed. Note that if you
            want to shard a tensor on a dimension that is not evenly divisible by
            the number of devices in that mesh dimension, we use ``torch.chunk``
            semantic to shard the tensor and scatter the shards. The uneven sharding
            behavior is experimental and subject to change.
        device_mesh (:class:`DeviceMesh`, optional): DeviceMesh to distribute the
            tensor, if not specified, must be called under a DeviceMesh context
            manager, default: None
        placements (List[:class:`Placement`], optional): the placements that
            describes how to place the tensor on DeviceMesh, must have the same
            number of elements as ``device_mesh.ndim``. If not specified, we will
            by default replicate the tensor across the ``device_mesh`` from the
            first rank of each dimension of the `device_mesh`.

    Keyword args:
        src_data_rank (int, optional): the rank of the source data for the logical/global tensor, it is
            used by :meth:`distribute_tensor` to scatter/broadcast the shards/replicas to other ranks.
            By default, we use ``group_rank=0`` on each DeviceMesh dimension as the source data to preserve
            the single-device semantic. If passing ``None`` explicitly, :meth:`distribute_tensor` simply uses
            its local data instead of trying to preserve the single-device semantic via scatter/broadcast.
            Default: 0

    Returns:
        A :class:`DTensor` or ``XLAShardedTensor`` object.

    Raises:
        ValueError: If ``placements`` contains mixed :class:`Partial` reduce types
            (e.g., both ``Partial("sum")`` and ``Partial("max")``). All Partial
            placements must use the same reduce operation.

    .. note::
        When initialize the DeviceMesh with the ``xla`` device_type, ``distribute_tensor``
        return `XLAShardedTensor` instead. see `this issue <https://github.com/pytorch/pytorch/issues/92909>`__
        for more details. The XLA integration is experimental and subject to change.
    """

    torch._C._log_api_usage_once("torch.dtensor.distribute_tensor")

    # get default device mesh if there's nothing specified
    device_mesh = device_mesh or _mesh_resources.get_current_mesh()
    device_type = device_mesh.device_type
    if device_type == "xla":
        try:
            # call PyTorch/XLA SPMD for `xla` backend type device mesh.
            # This returns XLAShardedTensor
            from torch_xla.distributed.spmd import (  # type:ignore[import]
                xla_distribute_tensor,
            )

            return xla_distribute_tensor(tensor, device_mesh, placements)  # type:ignore[return-value]
        except ImportError as e:
            msg = "To use DTensor API with xla, you must install the torch_xla package!"
            raise ImportError(msg) from e

    if not tensor.is_leaf:
        raise RuntimeError(
            "`distribute_tensor` should be used to distribute leaf tensors! but found non-leaf tensor!"
        )

    # convert tensor to the corresponding device type if it's not in that device type
    if device_type != tensor.device.type and not tensor.is_meta:
        tensor = tensor.to(device_type)

    # set default placements to replicated if not specified
    if placements is None:
        placements = [Replicate() for _ in range(device_mesh.ndim)]

    if len(placements) != device_mesh.ndim:
        raise ValueError(
            f"`placements` must have the same length as `device_mesh.ndim`! "
            f"Found placements length: {len(placements)}, and device_mesh.ndim: {device_mesh.ndim}."
        )

    # Validate that placements don't contain mixed Partial reduce types
    assert_no_mixed_partial_types(placements)
    if isinstance(tensor, DTensor):
        # if the tensor is already a DTensor, we need to check:
        # 1. if the we can further shard this DTensor if the two device mesh belong to
        #   the same parenet mesh and further sharding is possible.
        # 2. check if device mesh and placements are the same
        if tensor.device_mesh != device_mesh:
            raise ValueError(
                f"Cannot distribute a DTensor with device mesh {tensor.device_mesh} "
                f"to a different device mesh {device_mesh}."
            )
        if tensor.placements != tuple(placements):
            raise ValueError(
                f"Cannot distribute a DTensor with placements {tensor.placements} "
                f"to a different placements {placements}. do you want to call "
                f"`redistribute` instead?"
            )
        return tensor

    local_tensor = tensor.detach()

    # TODO(xilun): address sharding order
    # distribute the tensor according to the placements.
    placements = list(placements)
    for idx, placement in enumerate(placements):
        if isinstance(placement, Shard | _StridedShard):
            placement_dim = (
                placement.dim + tensor.ndim if placement.dim < 0 else placement.dim
            )
            if isinstance(placement, Shard):
                local_tensor = Shard._make_shard_tensor(
                    placement_dim, local_tensor, device_mesh, idx, src_data_rank
                )
                placements[idx] = Shard(placement_dim)
            else:
                local_tensor = _StridedShard._make_shard_tensor(
                    placement_dim,
                    local_tensor,
                    device_mesh,
                    idx,
                    src_data_rank,
                    split_factor=placement.split_factor,
                )
                placements[idx] = _StridedShard(
                    placement_dim, split_factor=placement.split_factor
                )
        elif isinstance(placement, Replicate):
            local_tensor = Replicate._make_replicate_tensor(
                local_tensor, device_mesh, idx, src_data_rank
            )
        elif isinstance(placement, Partial):
            local_tensor = Replicate._make_replicate_tensor(
                local_tensor, device_mesh, idx, src_data_rank
            )
            local_tensor = placement._partition_value(local_tensor, device_mesh, idx)
        else:
            raise RuntimeError(
                f"Trying to distribute tensor with unsupported placements {placement} on device mesh dimension {idx}!"
            )
    placements = tuple(placements)

    if local_tensor is None:
        raise AssertionError("distributing a tensor should not be None")
    # detach the local tensor passed to DTensor since after the construction
    # of DTensor, autograd would work on top of DTensor instead of local tensor
    spec = DTensorSpec(
        mesh=device_mesh,
        placements=placements,
        tensor_meta=TensorMeta(
            shape=tensor.size(),
            stride=tensor.stride(),
            dtype=tensor.dtype,
        ),
    )
    # pyrefly: ignore [bad-argument-type]
    return DTensor(
        # pyrefly: ignore [bad-argument-count]
        local_tensor.requires_grad_(tensor.requires_grad),
        spec,
        # pyrefly: ignore [unexpected-keyword]
        requires_grad=tensor.requires_grad,
    )