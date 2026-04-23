def fully_shard(
    module,
    *,
    mesh: DeviceMesh | None = None,
    reshard_after_forward: bool | int | None = None,
    shard_placement_fn: Callable[[nn.Parameter], ShardPlacementFnResult] | None = None,
    mp_policy: MixedPrecisionPolicy = MixedPrecisionPolicy(),
    offload_policy: OffloadPolicy = OffloadPolicy(),
    ignored_params: set[nn.Parameter] | None = None,
    dp_mesh_dims: DataParallelMeshDims | None = None,
):
    """
    Apply fully sharded data parallelism (FSDP) to ``module``, where FSDP
    shards module parameters, gradients, and optimizer states across data
    parallel workers to save memory at the cost of communication.

    At initialization, FSDP shards the module's parameters across the data
    parallel workers given by ``mesh``. Before forward, FSDP all-gathers the
    sharded parameters across the data-parallel workers to get the unsharded
    parameters for forward computation. If ``reshard_after_forward`` is
    ``True``, then FSDP frees the unsharded parameters after forward and
    re-all-gathers them in backward before gradient computation. After gradient
    computation, FSDP frees the unsharded parameters and reduce-scatters the
    unsharded gradients across data-parallel workers.

    This implementation represents the sharded parameters as :class:`DTensor` s
    sharded on dim-0, while the unsharded parameters will be like the original
    parameters on ``module`` (e.g. :class:`torch.Tensor` if originally
    :class:`torch.Tensor`). A module
    `forward pre-hook <https://pytorch.org/docs/main/generated/torch.nn.Module.html#torch.nn.Module.register_forward_pre_hook>`_
    on ``module`` all-gathers the parameters, and a module
    `forward hook <https://pytorch.org/docs/main/generated/torch.nn.Module.html#torch.nn.Module.register_forward_hook>`_
    on ``module`` frees them (if needed). Similar backward hooks all-gather
    parameters and later free parameters and reduce-scatter gradients.

    Since grouping multiple tensors together for one collective is critical for
    communication efficiency, this implementation makes this grouping first
    class. Calling :meth:`fully_shard` on ``module`` constructs one group that
    includes the parameters in ``module.parameters()`` except those already
    assigned to a group from an earlier call on a submodule. This means that
    :meth:`fully_shard` should be called bottom-up on your model. Each group's
    parameters are all-gathered in one collective, and its gradients are
    reduce-scattered in one collective. Partitioning the model into multiple
    groups ("layer by layer") allows for peak memory savings and communication/computation
    overlap. Users generally should *not* call :meth:`fully_shard` only on the
    topmost root module.

    Args:
        module (Union[nn.Module, List[nn.Module]): The module or modules to
            shard with FSDP and group together for communication.
        mesh (Optional[DeviceMesh]): This data parallel mesh defines the
            sharding and device. If 1D, then parameters are fully sharded
            across the 1D mesh (FSDP) with ``(Shard(0),)`` placement. If 2D,
            then parameters are sharded across the 1st dim and replicated
            across the 0th dim (HSDP) with ``(Replicate(), Shard(0))``
            placement. The mesh's device type gives the device type used for
            communication; if a CUDA or CUDA-like device type, then we use the
            current device.
        reshard_after_forward (Optional[Union[bool, int]]): This controls the parameter
            behavior after forward and can trade off memory and communication:

            - If ``True``, then this reshards parameters after forward and
              re-all-gathers in backward.
            - If ``False``, then this keeps the unsharded parameters in memory
              after forward and avoids the all-gather in backward. For best performance,
              we usually set ``False`` for the root module, because the root module
              is typically required immediately when the backward pass begins.
            - If ``None``, it is set to ``True`` for non-root modules and ``False``
              for root modules.
            - If an ``int``, then this represents the world size to reshard to
              after forward. It should be a non-trivial divisor of the ``mesh``
              shard dim size (i.e. excluding 1 and the dim size itself). A
              choice may be the intra-node size (e.g. ``torch.cuda.device_count()``).
              This allows the all-gather in backward to be over a smaller world
              size at the cost of higher memory usage than setting to ``True``.
            - After forward, the parameters registered to the module depend on
              to this: The registered parameters are the sharded parameters if
              ``True``; unsharded parameters if ``False``; and the parameters
              resharded to the smaller mesh otherwise. To modify the parameters
              between forward and backward, the registered parameters must be
              the sharded parameters. For ``False`` or an ``int``, this can be
              done by manually resharding via :meth:`reshard`.
        shard_placement_fn (Optional[Callable[[nn.Parameter], Optional[Shard | ShardPlacementResult]]]):
            This callable can be used to override the sharding placement and/or
            mesh for a parameter. It can return:

            - ``None``: Use default sharding (Shard(0)) on the mesh passed to
              ``fully_shard``.
            - :class:`Shard`: Shard the parameter on the specified dimension
              using the mesh passed to ``fully_shard``.
            - :class:`ShardPlacementResult`: Specify both the shard placement
              and a custom :class:`FSDPMeshInfo`. This allows different
              parameters to be sharded across different process groups, enabling
              use cases like Mixture of Experts where expert params use a
              different mesh than regular params.

            If sharding on a nonzero dim, we currently require even sharding,
            i.e. the tensor dim size on that dim must be divisible by the FSDP
            shard mesh size.
        mp_policy (MixedPrecisionPolicy): This controls the mixed precision
            policy, which offers parameter/reduction mixed precision for this
            module. See :class:`MixedPrecisionPolicy` for details.
        offload_policy (OffloadPolicy): This controls the offloading policy,
            which offers parameter/gradient/optimizer state offloading. See
            :class:`OffloadPolicy` and its subclasses for details.
        ignored_params: Optional(Set[nn.Parameter]): The set of parameters to be
            ignored by FSDP. They will not be sharded, nor moved to the device
            during init, nor have their gradients reduced in backward.
        dp_mesh_dims (Optional[DataParallelMeshDims]): When provided,
            ``mesh`` is treated as the full SPMD mesh, and parameters should be
            DTensors on this mesh with ``Replicate()`` on all DP dimensions.
            The ``shard`` field names which dim(s) FSDP shards on (multiple
            dims are flattened). The ``replicate`` field names the HSDP
            replication dim(s) (multiple dims are flattened).

    Returns:
        FSDPModule: The module with FSDP applied (in-place).
    """
    torch._C._log_api_usage_once("torch.distributed.fsdp.fully_shard")
    _validate_module(module, "fully_shard")
    mesh = mesh or _init_default_mesh()
    _validate_mesh(mesh, dp_mesh_dims)
    mesh_info = _get_mesh_info(mesh, dp_mesh_dims)
    device = _get_device_from_mesh(mesh)
    auto_reshard_after_forward = reshard_after_forward is None
    # If the user does not provide ``reshard_after_forward``, we set it to True.
    # During lazy_init, we identify which module is the root and override its value to False
    if isinstance(mesh_info, FSDPMeshInfo):
        if (
            mesh_info.is_spmd_mesh
            and not isinstance(reshard_after_forward, bool)
            and isinstance(reshard_after_forward, int)
        ):
            raise NotImplementedError(
                "reshard_after_forward as int is not yet supported with "
                "SPMD mesh (dp_mesh_dims)"
            )
        post_forward_mesh_info = _get_post_forward_mesh_info(
            reshard_after_forward if not auto_reshard_after_forward else True,  # type: ignore[arg-type]
            mesh_info,
        )
    else:
        # DDPMeshInfo: no sharding, so no post-forward resharding needed
        post_forward_mesh_info = None
    arg_module, modules, managed_modules, params, buffers = _get_modules_and_states(
        module, device, ignored_params
    )
    state = fully_shard.state(modules[0])  # type: ignore[attr-defined]
    state.init(modules, device, mp_policy, auto_reshard_after_forward)

    _init_param_group(
        state,
        params,
        modules,
        mesh_info,
        post_forward_mesh_info,
        device,
        shard_placement_fn,
        mp_policy,
        offload_policy,
        reshard_after_forward=reshard_after_forward
        if not auto_reshard_after_forward
        else True,
    )

    # For Dynamo
    for managed_module in managed_modules:
        managed_module._is_fsdp_managed_module = True  # type: ignore[assignment]
        managed_module._fsdp_use_orig_params = True  # type: ignore[assignment]

    # Place FSDP leftmost for highest priority in the method resolution order
    _apply_to_module(
        modules, cls_to_fsdp_cls, FSDPModule, "FSDP", _unimplemented_deepcopy
    )
    return arg_module