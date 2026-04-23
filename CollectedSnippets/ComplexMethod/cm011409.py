def from_local(
        local_tensor: torch.Tensor,
        device_mesh: DeviceMesh | None = None,
        placements: Sequence[Placement] | None = None,
        *,
        run_check: bool = False,
        shape: torch.Size | None = None,
        stride: tuple[int, ...] | None = None,
        grad_placements: Sequence[Placement] | None = None,
    ) -> "DTensor":
        """
        Create a :class:`DTensor` from a local torch.Tensor on each rank
        according to the ``device_mesh`` and ``placements`` specified.

        Args:
            local_tensor (torch.Tensor): local torch.Tensor on each rank.
            device_mesh (:class:`DeviceMesh`, optional): DeviceMesh to place the
                tensor, if not specified, must be called under a DeviceMesh
                context manager, default: None
            placements (List[:class:`Placement`], optional): the placements that
                describes how to place the local torch.Tensor on DeviceMesh, must
                have the same number of elements as ``device_mesh.ndim``.

        Keyword args:
            run_check (bool, optional): at a cost of extra communications, perform
                sanity check across ranks to check each local tensor's meta information
                to ensure correctness. If have :class:`Replicate` in ``placements``, the
                data on first rank of the device mesh dimension will be broadcasted
                to other ranks. default: False
            shape (torch.Size, optional): A List of int which specifies the size of
                DTensor which build on top of `local_tensor`. Note this needs to be
                provided if the shape of ``local_tensor`` are different across the ranks.
                If not provided, ``shape`` will be computed assuming the given distributed
                tensor is evenly sharded across ranks. default: None
            stride (tuple, optional): A List of int which specifies the stride of DTensor.
                If not provided, ``stride`` will be computed assuming the given distributed
                tensor is evenly sharded across ranks. default: None
            grad_placements (List[:class:`Placement`], optional): specifies the expected
                input gradient placements. The input gradient (a plain tensor) will be
                redistributed to this placement before exiting DTensor. If not
                specified, follows the default placement guarantees below. default: None

        Returns:
            A :class:`DTensor` object

        Raises:
            ValueError: If ``placements`` contains mixed :class:`Partial` reduce types
                (e.g., both ``Partial("sum")`` and ``Partial("max")``). All Partial
                placements must use the same reduce operation.

        .. note:: When ``run_check=False``, it is the user's responsibility to ensure the
            local tensor passed in is correct across ranks (i.e. the tensor is sharded for
            the ``Shard(dim)`` placement or replicated for the ``Replicate()`` placement).
            If not, the behavior of the created DTensor is undefined.

        .. note:: ``from_local`` is differentiable, the `requires_grad` of the created
            `DTensor` object will depend on if `local_tensor` requires_grad or not.

        .. note:: During backward, ``from_local`` provides the following gradient placement
            guarantees. For each mesh dimension, the gradient placement maps as follows:

            +---------------------+--------------------+
            | Forward Placement   | Gradient Placement |
            +=====================+====================+
            | ``Shard``           | ``Shard``          |
            +---------------------+--------------------+
            | ``Replicate``       | ``Replicate``      |
            +---------------------+--------------------+
            | ``Partial``         | ``Replicate``      |
            +---------------------+--------------------+

            When the forward placement is :class:`Partial`, we always redistribute the gradient
            to :class:`Replicate` instead of keeping it :class:`Partial`. This may not be the most
            efficient option, but it avoids ambiguity and provides clearer gradient semantics to users.
        """
        # `local_tensor` argument cannot be DTensor
        if isinstance(local_tensor, DTensor):
            raise RuntimeError(
                f"the local_tensor argument only accepts torch.Tensor but got {type(local_tensor)} value."
            )

        # if same shape/dtype, no need to run_check, if not, must allgather
        # the metadatas to check the size/dtype across ranks
        # There should be no data communication unless there's replication
        # strategy, where we broadcast the replication from the first rank
        # in the mesh dimension
        device_mesh = device_mesh or _mesh_resources.get_current_mesh()
        device_type = device_mesh.device_type

        # convert the local tensor to desired device base on device mesh's device_type
        if device_type != local_tensor.device.type and not local_tensor.is_meta:
            local_tensor = local_tensor.to(device_type)

        # set default placements to replicated if not specified
        if placements is None:
            placements = [Replicate() for _ in range(device_mesh.ndim)]
        else:
            placements = list(placements)
            for idx, placement in enumerate(placements):
                # normalize shard dim to be positive
                if isinstance(placement, Shard | _StridedShard):
                    if placement.dim < 0:
                        normalized_dim = placement.dim + local_tensor.ndim
                        if type(placement) is _StridedShard:
                            placements[idx] = _StridedShard(
                                normalized_dim, split_factor=placement.split_factor
                            )
                        elif type(placement) is Shard:
                            placements[idx] = Shard(normalized_dim)

        # Validate that placements don't contain mixed Partial reduce types
        assert_no_mixed_partial_types(placements)

        # `from_local` is differentiable, and the gradient of the dist tensor this function
        # created should flow back the gradients to the local_tensor, so we call an autograd
        # function to construct the dist tensor instead.
        return _FromTorchTensor.apply(  # pyre-ignore[16]: autograd func
            local_tensor,
            device_mesh,
            tuple(placements),
            run_check,
            shape,
            stride,
            tuple(grad_placements) if grad_placements is not None else None,
        )