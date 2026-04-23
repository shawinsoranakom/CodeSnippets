def __init__(
        self,
        module,
        device_ids=None,
        output_device=None,
        dim=0,
        broadcast_buffers=True,
        init_sync=True,
        process_group=None,
        bucket_cap_mb=None,
        find_unused_parameters=False,
        check_reduction=False,
        gradient_as_bucket_view=False,
        static_graph=False,
        delay_all_reduce_named_params=None,
        param_to_hook_all_reduce=None,
        mixed_precision: _MixedPrecision | None = None,
        device_mesh=None,
        skip_all_reduce_unused_params=False,
        bucket_cap_mb_list: list[int] | None = None,
        batched_grad_copy=False,
    ):
        super().__init__()
        Joinable.__init__(self)
        self._use_python_reducer = (
            torch._dynamo.utils.get_optimize_ddp_mode() == "python_reducer"
        )
        self.logger: dist.Logger | None = None
        if bool(delay_all_reduce_named_params is not None) != bool(
            param_to_hook_all_reduce is not None
        ):
            self._log_and_throw(
                ValueError,
                "delay_all_reduce_named_params and param_to_hook_all_reduce "
                "need to be set at the same time.",
            )

        if process_group and device_mesh is not None:
            raise RuntimeError(
                "Cannot specify both process_group and device_mesh arguments."
            )
        elif process_group is None and device_mesh is None:
            self.process_group = _get_default_group()
        elif device_mesh is None:
            # pyrefly: ignore [bad-assignment]
            self.process_group = process_group
        else:
            if device_mesh.ndim != 1:
                raise RuntimeError(
                    f"Only 1D device mesh is supported, but got {device_mesh}."
                )
            self.device_mesh = device_mesh
            self.process_group = device_mesh.get_group(mesh_dim=0)

            root_mesh = device_mesh._get_root_mesh()
            # if a root mesh is not the same as device_mesh,
            # meaning the device_mesh is sliced out from the root mesh.
            if root_mesh != device_mesh:
                # TODO: This is a temporary work around to enable DDP + TP.
                # We should do the logic in DDP so that the 2D implementation is
                # sound and the state_dict works out of the box.
                # This has to be done before check UninitializedParameter.
                from torch.distributed.tensor.parallel.ddp import (
                    _pre_dp_module_transform,
                )

                _pre_dp_module_transform(module)

        self._delay_all_reduce_params = []
        if hasattr(module, "_ddp_params_and_buffers_to_ignore"):
            self.parameters_to_ignore = set(module._ddp_params_and_buffers_to_ignore)
        else:
            self.parameters_to_ignore = set()
        if delay_all_reduce_named_params is not None:
            for name, param in delay_all_reduce_named_params:
                self.parameters_to_ignore.add(name)
                self._delay_all_reduce_params.append(param)

        self._module_parameters = [
            p
            for n, p in module.named_parameters()
            if n not in self.parameters_to_ignore
        ]
        if not any(p.requires_grad for p in self._module_parameters):
            if len(self._delay_all_reduce_params):
                logger.info("Delay the AllReduce of all parameters.")
            else:
                self._log_and_throw(
                    RuntimeError,
                    "DistributedDataParallel is not needed when a module "
                    "doesn't have any parameter that requires a gradient.",
                )

        if device_ids is not None and len(device_ids) > 1:
            self._log_and_throw(
                ValueError,
                "device_ids can only be None or contain a single element.",
            )

        self.is_multi_device_module = (
            len({p.device for p in self._module_parameters}) > 1
        )
        distinct_device_types = {
            p.device.type for p in self._module_parameters if p.device is not None
        }
        if len(distinct_device_types) != 1:
            self._log_and_throw(
                ValueError,
                "DistributedDataParallel's input module must be on "
                f"the same type of devices, but input module parameters locate in {distinct_device_types}.",
            )

        self.device_type = next(iter(distinct_device_types))

        if (
            device_ids is None
            or len(device_ids) == 0  # For backward compatibility.
            or self.device_type == "cpu"
            or self.is_multi_device_module
        ):
            if device_ids or output_device:
                devices = {p.device for p in self._module_parameters}
                self._log_and_throw(
                    ValueError,
                    "DistributedDataParallel device_ids and output_device arguments "
                    "only work with single-device/multiple-device GPU modules or CPU modules, "
                    f"but got device_ids {device_ids}, output_device {output_device}, "
                    f"and module parameters {devices}.",
                )

            self.device_ids = None
            self.output_device = None
        else:
            self.device_ids = [_get_device_index(x, True) for x in device_ids]

            if output_device is None:
                output_device = device_ids[0]

            self.output_device = _get_device_index(output_device, True)

        self.static_graph = False
        self.dim = dim
        self.module = module
        self.device = next(iter(self._module_parameters)).device
        self.broadcast_buffers = broadcast_buffers
        self.find_unused_parameters = find_unused_parameters
        self.require_backward_grad_sync = True
        self.require_forward_param_sync = True
        self.gradient_as_bucket_view = gradient_as_bucket_view
        self.batched_grad_copy = batched_grad_copy
        self.mixed_precision = mixed_precision
        if self.mixed_precision is not None:
            logger.warning("Received mixed precision config %s", self.mixed_precision)

        if check_reduction:
            # This argument is no longer used since the reducer
            # will ensure reduction completes even if some parameters
            # do not receive gradients.
            warnings.warn(
                "The `check_reduction` argument in `DistributedDataParallel` "
                "module is deprecated. Please avoid using it.",
                FutureWarning,
                stacklevel=2,
            )

        # Check that a module does not have Uninitialized parameters
        for param in self._module_parameters:
            if isinstance(param, torch.nn.parameter.UninitializedParameter):
                self._log_and_throw(
                    RuntimeError,
                    "Modules with uninitialized parameters can't be used with `DistributedDataParallel`. "
                    "Run a dummy forward pass to correctly initialize the modules",
                )
        # used for intra-node param sync and inter-node sync as well
        self.broadcast_bucket_size = 250 * 1024 * 1024

        # Initialize bucket capacity configuration using the factory method
        self._bucket_config = _BucketCapacityConfig.create(
            bucket_cap_mb=bucket_cap_mb,
            bucket_cap_mb_list=bucket_cap_mb_list,
            use_python_reducer=self._use_python_reducer,
        )
        # Expose config values as instance attributes for backward compatibility
        # TODO: Remove in the future
        self.bucket_bytes_cap = self._bucket_config.bucket_bytes_cap
        self.bucket_bytes_cap_list = list(self._bucket_config.per_bucket_bytes_caps)
        self.bucket_bytes_cap_default = (
            self._bucket_config.first_bucket_bytes_cap
            < self._bucket_config.bucket_bytes_cap
        )
        bucket_cap_mb = self._bucket_config.bucket_cap_mb

        # Whether to perform input tensor CPU to GPU copies on a side-stream
        self.use_side_stream_for_tensor_copies = (
            os.environ.get("PYTORCH_DDP_USE_SIDE_STREAM", "1") == "1"
        )

        # Initialize gradient buffers and register all reduce hook
        self._delay_grad_buffer: torch.Tensor | None = None
        self._delay_grad_views: list[torch.Tensor] = []
        self._delay_all_reduce_all_params = False
        if len(self._delay_all_reduce_params) != 0:
            self._register_delay_all_reduce_hook(
                bucket_cap_mb=bucket_cap_mb,
                param_to_hook_all_reduce=param_to_hook_all_reduce,
                device_ids=device_ids,
            )
            if self._delay_all_reduce_all_params:
                return

        self.skip_all_reduce_unused_params = skip_all_reduce_unused_params

        # Build parameters for reducer.
        parameters, expect_sparse_gradient = self._build_params_for_reducer()

        # All collectives during initialization are gated by this flag.
        if init_sync:
            # Verify model equivalence.
            _verify_param_shape_across_processes(self.process_group, parameters)
            # Sync params and buffers. Ensures all DDP models start off at the same value.
            _sync_module_states(
                module=self.module,
                process_group=self.process_group,
                broadcast_bucket_size=self.broadcast_bucket_size,
                src=0,
                params_and_buffers_to_ignore=self.parameters_to_ignore,
                broadcast_buffers=self.broadcast_buffers,
            )

        # In debug mode, build a mapping of parameter index -> parameter.
        param_to_name_mapping = self._build_debug_param_to_name_mapping(parameters)

        # Builds reducer.
        self._ddp_init_helper(
            parameters,
            expect_sparse_gradient,
            param_to_name_mapping,
            static_graph,
        )
        self._comm_hooks: list[tuple[Callable, object]] = []

        if self.mixed_precision is not None:
            _setup_mixed_precision_params(self.mixed_precision, self.module)
            _cast_buffers(self.mixed_precision, self.module)
            # Stream used for async low precision copies.
            self._mp_stream = torch.Stream()
            self._submodule_to_event = defaultdict(deque)  # type: ignore[var-annotated]
            # Add forward pre-hook to root module to kick off copies to lower
            # precision.
            self.module.register_forward_pre_hook(
                self._root_copy_hook, prepend=False, with_kwargs=True
            )
            # Add forward pre hook to all submodules to wait for copy events
            # before running computation.
            for module in self.module.modules():
                module.register_forward_pre_hook(
                    self._module_wait_for_copy_hook,
                    prepend=False,
                    with_kwargs=True,
                )
            # Set up callbacks in backward to upcast and use full precision
            # params. TODO (rohan-varma): Make this compose with general
            # comm hooks and apply_optimizer_in_backward. Importing inline to
            # avoid circular import issue.
            from torch.distributed.algorithms.ddp_comm_hooks.mixed_precision_hooks import (
                _AllreduceUpcastHookState,
                _reducer_allreduce_and_upcast_hook,
            )

            upcast_hook_state = _AllreduceUpcastHookState(
                ddp_weakref=weakref.ref(self),
                upcast_stream=torch.Stream(),
            )
            self.register_comm_hook(
                upcast_hook_state,
                _reducer_allreduce_and_upcast_hook,
            )
            # Inform reducer of reduced precision param dtype for correctness
            # of type checks between gradient and bucket.
            self.reducer._set_mixed_precision_param_dtype(  # type: ignore[attr-defined]
                self.mixed_precision.param_dtype
            )

        self._has_rebuilt_buckets = False

        if static_graph:
            self._set_static_graph()

        self._lazy_init_ran = False

        # Register the AccumulateGrad post hooks if optimize_ddp is
        # True. The hooks will be deregistered if compiled_autograd is not
        # enabled.
        self._accum_grad_hooks: list[RemovableHandle] = []
        if self._use_python_reducer:
            # pyrefly: ignore [bad-assignment]
            torch._inductor.config._fuse_ddp_communication = True
            # pyrefly: ignore [bad-assignment]
            torch._inductor.config._fuse_ddp_bucket_size = bucket_cap_mb
            # Directly adding this to the trace rule will disturb the users
            # who are using DDPOptimizer.
            torch._dynamo.trace_rules.LEGACY_MOD_INLINELIST.add(
                "torch.nn.parallel.distributed"
            )
            torch._dynamo.trace_rules.get_legacy_mod_inlinelist.cache_clear()
            # NOTE: we should init these lazily
            self._register_accum_grad_hook()

        # Whether or not DDPSink performs a clone.
        self._ddp_sink_clone = True