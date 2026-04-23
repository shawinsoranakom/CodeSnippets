def _verify_options(
    model: nn.Module,
    optims: tuple[torch.optim.Optimizer, ...],
    optim_only: bool,
    *,
    submodules: set[nn.Module] | None = None,
    options: StateDictOptions | None = None,
) -> _StateDictInfo:
    """
    Verify the model and options passed by the user and generates _StateDictInfo.
    """
    if submodules:
        warnings.warn(
            "Getting submodules only model/optim state_dict is deprecated and "
            "will be removed in 2.5. This feature can be achieved by manually "
            "filtering out the state_dict returned from get_state_dict.",
            FutureWarning,
            stacklevel=2,
        )
    if optim_only and not optims:
        raise RuntimeError(
            "Optimizers are not passed in but optim_only is set to True."
        )

    options = options or StateDictOptions()

    fqn_param_mapping: dict[str | torch.Tensor, set[str] | torch.Tensor] = {}
    shared_params_mapping: dict[str | torch.Tensor, set[str] | torch.Tensor] = {}
    for name, param in _iterate_valid_model_state(model):
        if isinstance(param, _EXTRA_STATE):
            continue

        fqns = _get_fqns(model, name)
        fqn = fqn_param_mapping.get(param)
        if fqn is not None:
            cast(set[str], fqn_param_mapping[param]).update(fqns)
            shared_params_mapping[param] = fqn_param_mapping[param]
        else:
            # We need to do copy as _get_fqns is lru_cached
            fqn_param_mapping[param] = fqns.copy()
        for fqn in fqns:
            if not isinstance(param, _EXTRA_STATE):
                fqn_param_mapping[fqn] = param

    for param_, fqns_ in list(shared_params_mapping.items()):
        for fqn in fqns_:
            shared_params_mapping[fqn] = cast(torch.Tensor, param_)

    submodule_prefixes: set[str] = set()
    if submodules:
        submodules = set(submodules)
        for name, module in model.named_modules():
            if module not in submodules:
                continue
            fqns = _get_fqns(model, name)
            if len(fqns) != 1:
                raise AssertionError("Submodule FQN should only have 1 instance")
            submodule_prefixes.update(f"{fqn}." for fqn in fqns)

    if options.broadcast_from_rank0 and not options.full_state_dict:
        raise ValueError(
            "full_state_dict must be True when broadcast_from_rank0 is True."
        )
    fsdp_modules = FSDP.fsdp_modules(model)
    state_dict_config: StateDictConfig
    optim_state_dict_config: OptimStateDictConfig
    fsdp_context: Callable
    if fsdp_modules:
        # FSDP API only work if at least one FSDP instance exists.
        if options.full_state_dict:
            state_dict_config = FullStateDictConfig(
                offload_to_cpu=options.cpu_offload, rank0_only=options.cpu_offload
            )
            optim_state_dict_config = FullOptimStateDictConfig(
                offload_to_cpu=options.cpu_offload,
                rank0_only=(options.cpu_offload or options.broadcast_from_rank0),
            )
            state_dict_type = StateDictType.FULL_STATE_DICT
        else:
            state_dict_config = ShardedStateDictConfig(
                offload_to_cpu=options.cpu_offload,
            )
            optim_state_dict_config = ShardedOptimStateDictConfig(
                offload_to_cpu=options.cpu_offload,
            )
            state_dict_type = StateDictType.SHARDED_STATE_DICT

        @contextlib.contextmanager
        def fsdp_state_dict_type_without_warning(
            module,
            state_dict_type,
            state_dict_config,
            optim_state_dict_config,
        ):
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="FSDP.state_dict_type", category=FutureWarning
                )
                with FSDP.state_dict_type(
                    module=module,
                    state_dict_type=state_dict_type,
                    state_dict_config=state_dict_config,
                    optim_state_dict_config=optim_state_dict_config,
                ):
                    yield

        fsdp_context = functools.partial(
            fsdp_state_dict_type_without_warning,
            module=model,
            state_dict_type=state_dict_type,
            state_dict_config=state_dict_config,
            optim_state_dict_config=optim_state_dict_config,
        )
    else:
        fsdp_context = contextlib.nullcontext

    return _StateDictInfo(
        **asdict(options),
        fqn_param_mapping=fqn_param_mapping,
        shared_params_mapping=shared_params_mapping,
        submodule_prefixes=submodule_prefixes,
        fsdp_context=fsdp_context,
        fsdp_modules=cast(list[nn.Module], fsdp_modules),
        handle_model=not optim_only,
        handle_optim=(len(optims) > 0),
    )