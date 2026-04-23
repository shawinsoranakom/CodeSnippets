def _convert_state_with_orig_params(
    all_optim_state_keys: list[_OptimStateKey],
    optim_state_key_to_param_key: dict[_OptimStateKey, int | str],
    fqn_to_fsdp_param_info: dict[str, FSDPParamInfo],
    optim_state_dict: dict[str | int, Any],
    to_save: bool,
    shard_state: bool,
    cpu_offload: bool = True,
) -> dict[str, Any]:
    fsdp_osd_state: dict[str, Any] = {}
    # This variable is used to deduplicate the FSDPParamInfo as one FSDPParamInfo
    # usually corresponds to multiple parameters. We could not use FSDPParamInfo
    # as the key because FSDPParamInfo is not hashable. As a result, we fall back
    # to `id(FSDPParamInfo)`, which the type is an integer.
    all_states: dict[int, dict[str, Any]] = {}
    # Iterate in rank 0's flat parameter ID order to ensure aligned all-gathers
    # across ranks
    for optim_state_key in all_optim_state_keys:
        param_key: str | int | None = optim_state_key_to_param_key.get(optim_state_key)

        if param_key is None and not optim_state_key.is_fsdp_managed:
            continue

        if optim_state_key.is_fsdp_managed:
            fqn = optim_state_key.unflat_param_names[0]
            fsdp_param_info = fqn_to_fsdp_param_info.get(fqn)
            if fsdp_param_info is None:
                # This can happen if the not all FSDP instances have all the
                # parameters. This can happen with FSDP + some MPMD style
                # parallelism.

                # TODO: it is unclear if we need to do the same check with
                # non-FSDP managed keys.
                continue
            state = {} if param_key is None else optim_state_dict[param_key]
            if id(fsdp_param_info) not in all_states:
                all_states[id(fsdp_param_info)] = {}
            all_states[id(fsdp_param_info)][fqn] = state

        elif to_save:
            if len(optim_state_key.unflat_param_names) != 1:
                raise AssertionError(
                    f"Expected len(optim_state_key.unflat_param_names) == 1, got {len(optim_state_key.unflat_param_names)}"
                )
            unflat_param_name = optim_state_key.unflat_param_names[0]
            with SimpleProfiler.profile("none_fsdp_managed_copy"):
                param_key = cast(str | int, param_key)
                fsdp_osd_state[unflat_param_name] = copy.copy(
                    optim_state_dict[param_key]
                )
                if cpu_offload:
                    for state_name, value in sorted_items(
                        fsdp_osd_state[unflat_param_name]
                    ):
                        if not torch.is_tensor(value):
                            continue
                        fsdp_osd_state[unflat_param_name][state_name] = value.cpu()

    # Instead of gathering the state of each parameter individually, we perform
    # the gathering  all at once to speed up the process.
    for _all_states in all_states.values():
        fqn = next(iter(_all_states.keys()))
        fsdp_param_info = fqn_to_fsdp_param_info[fqn]
        if len(fsdp_param_info.param_requires_grad) <= 0:
            raise AssertionError(
                "With use_orig_params, FSDPParamInfo should have requires_grad "
                "information. However, the length is zero."
            )
        for key, idx in fsdp_param_info.param_indices.items():
            if key in _all_states:
                continue
            if not fsdp_param_info.param_requires_grad[idx]:
                continue
            raise RuntimeError(
                f"{key} is not in the optimizer state. "
                "The FSDPParamInfo has the param keys "
                f"{sorted(fsdp_param_info.param_indices.keys())} while "
                "the optimizer has the param keys "
                f"{sorted(_all_states.keys())}."
            )
        fsdp_osd_state.update(
            _gather_all_orig_param_state(
                fsdp_param_info,
                _all_states,
                shard_state,
                to_save,
                cpu_offload,
            )
        )

    return fsdp_osd_state