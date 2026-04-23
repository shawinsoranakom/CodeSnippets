def _convert_state_with_flat_params(
    all_optim_state_keys: list[_OptimStateKey],
    optim_state_key_to_param_key: dict[_OptimStateKey, int | str],
    fqn_to_fsdp_param_info: dict[str, FSDPParamInfo],
    optim_state_dict: dict[str | int, Any],
    to_save: bool,
    shard_state: bool,
    cpu_offload: bool = True,
) -> dict[str, Any]:
    fsdp_osd_state: dict[str, Any] = {}
    # Iterate in rank 0's flat parameter ID order to ensure aligned all-gathers
    # across ranks
    for optim_state_key in all_optim_state_keys:
        param_key: str | int | None = optim_state_key_to_param_key.get(optim_state_key)

        if param_key is None:
            raise AssertionError(
                "If use_orig_params is False, we must be able to find the "
                f"corresponding param id. {optim_state_key} {param_key}"
            )

        if optim_state_key.is_fsdp_managed:
            # If there are multiple unflat_param_names (not use_orig_params),
            # they share the same FSDPParamInfo. So the first unflat_param_name
            # is sufficient to fetch the FSDPParamInfo.
            fqn = optim_state_key.unflat_param_names[0]
            fsdp_param_info = fqn_to_fsdp_param_info[fqn]
            unflat_state = _unflatten_optim_state(
                fsdp_param_info,
                optim_state_dict[param_key],
                to_save,
                shard_state,
                cpu_offload,
            )
            if to_save:
                if len(unflat_state) != len(optim_state_key.unflat_param_names):
                    raise AssertionError(
                        f"Expected len(unflat_state) == len(optim_state_key.unflat_param_names), "
                        f"got {len(unflat_state)} != {len(optim_state_key.unflat_param_names)}"
                    )
                fsdp_osd_state.update(
                    zip(
                        optim_state_key.unflat_param_names,
                        unflat_state,
                    )
                )
        elif to_save:
            if len(optim_state_key.unflat_param_names) != 1:
                raise AssertionError(
                    f"Expected len(optim_state_key.unflat_param_names) == 1, got {len(optim_state_key.unflat_param_names)}"
                )
            unflat_param_name = optim_state_key.unflat_param_names[0]
            fsdp_osd_state[unflat_param_name] = copy.copy(optim_state_dict[param_key])
            if cpu_offload:
                for state_name, value in sorted_items(
                    fsdp_osd_state[unflat_param_name]
                ):
                    if not torch.is_tensor(value):
                        continue
                    fsdp_osd_state[unflat_param_name][state_name] = value.cpu()

    return fsdp_osd_state