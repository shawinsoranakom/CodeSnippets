def __init__(
        self,
        params: Sequence[nn.Parameter | Tensor],
        fully_sharded_module: nn.Module,
        device: torch.device,
        sharding_strategy: HandleShardingStrategy,
        offload_params: bool,
        mp_param_dtype: torch.dtype | None,
        mp_reduce_dtype: torch.dtype | None,
        keep_low_precision_grads: bool,
        process_group: dist.ProcessGroup,
        use_orig_params: bool,
        *,
        fsdp_extension: FSDPExtensions | None = None,
    ):
        super().__init__()
        params = list(params)
        if len(params) == 0:
            raise ValueError(
                f"Cannot construct a {self.__class__.__name__} with an empty parameter list"
            )
        self._init_setattr_fns()
        self._skip_writeback_check = (
            os.environ.get(_FSDP_SKIP_WRITEBACK_CHECK, "") == "1"
        )
        self._use_full_prec_in_eval = (
            os.environ.get(_FSDP_USE_FULL_PREC_IN_EVAL, "") == "1"
        )
        self._use_fake_all_gather = os.environ.get(_FSDP_USE_FAKE_ALL_GATHER, "") == "1"
        self._use_fake_reduce = os.environ.get(_FSDP_USE_FAKE_REDUCE, "") == "1"
        if self._skip_writeback_check:
            _warn_skip_writeback_check(
                logger,
                f"Since {_FSDP_SKIP_WRITEBACK_CHECK}=1, FSDP will not check "
                "for parameter or gradient writeback. Changing parameter or "
                "gradient storages may lead to silent correctness errors.",
            )
        if self._use_fake_all_gather:
            _warn_use_fake_all_gather(
                logger,
                f"Since {_FSDP_USE_FAKE_ALL_GATHER}=1, FSDP will not execute "
                "all-gather ops. Your training will be incorrect, but "
                "can reveal how much time spent on all-gather ops.",
            )
        if self._use_fake_reduce:
            _warn_use_fake_reduce(
                logger,
                f"Since {_FSDP_USE_FAKE_REDUCE}=1, FSDP will not execute "
                "reduce-scatter ops. Your training will be incorrect, but "
                "can reveal how much time spent on reduce-scatter ops.",
            )
        # Only align addresses for `use_orig_params=True` (for now)
        align_addresses = use_orig_params
        self._init_get_unflat_views_fn(align_addresses)
        self.device = device
        self._device_handle = _FSDPDeviceHandle.from_device(self.device)
        self.process_group = process_group
        if self._use_fake_all_gather or self._use_fake_reduce:
            self._fake_process_group = FakeProcessGroup._create_internal(
                rank=process_group.rank(), world_size=process_group.size()
            )
        self.rank = process_group.rank()
        self.world_size = process_group.size()
        self._sharding_strategy = sharding_strategy
        self._offload_params = offload_params
        self._use_orig_params = use_orig_params
        self._keep_low_precision_grads = keep_low_precision_grads
        self._training_state = HandleTrainingState.IDLE
        self._debug_level = dist.get_debug_level()
        self._fully_sharded_module = fully_sharded_module
        # For strategies that do not free after forward, we skip using sharded
        # views after forward since the unsharded data exists. We still switch
        # `self.flat_param` to point to the sharded flat parameter since what
        # it points to parameterizes behavior. We use the following attribute
        # to track which tensor data the parameters are unsharded views into.
        self._unsharded_flat_param_for_skipped_views: Tensor | None = None
        # The index in the state's `all_handles`, which must be the
        # same across ranks for the execution order validation to work
        self._handle_index: int | None = None
        # Index in handles_to_pre_forward_order
        self._pre_forward_order_index: int | None = None
        # Index in `handles_post_forward_order`
        self._post_forward_index: int | None = None
        # Used for guarding against mistargeted forward prefetches
        self._needs_pre_forward_unshard = False
        # Used for guarding against mistargeted backward prefetches
        self._needs_pre_backward_unshard = False
        # Was the handle prefetched? Set on successful _prefetch_handle and unshard
        self._prefetched = False
        self._compute_stream: torch.Stream | None = None
        # Optimistically assume a valid input `params` and set dtype attributes
        # before `_init_flat_param()`, which performs the actual validation
        self._orig_param_dtype = params[0].dtype
        self._init_param_reduce_dtypes(mp_param_dtype, mp_reduce_dtype)
        if self._fwd_bwd_param_dtype is None:
            raise AssertionError("Expected _fwd_bwd_param_dtype to be not None")  # mypy
        self._aligned_numel = (
            _get_aligned_numel(unsharded_dtype=self._fwd_bwd_param_dtype)
            if align_addresses
            else 0
        )
        self._fsdp_extension = fsdp_extension
        self._init_flat_param_and_metadata(
            params,
            fully_sharded_module,
            self._aligned_numel,
            use_orig_params,  # type: ignore[arg-type]
        )
        self._use_unsharded_views(as_params=False)