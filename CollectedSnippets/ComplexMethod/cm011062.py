def _check_missing_keys_on_rank(
    r0_optim_state_keys: list[_OptimStateKey],
    optim_state_key_to_param_key: dict[_OptimStateKey, str | int],
    param_key_to_param: dict[str | int, nn.Parameter],
    group: dist.ProcessGroup | None,
) -> None:
    # Ensure that all ranks have at least the optimizer states needed by
    # rank 0's optimizer
    missing_keys: list[_OptimStateKey] = []
    for r0_optim_state_key in r0_optim_state_keys:
        if r0_optim_state_key not in optim_state_key_to_param_key:
            # A parameter from rank 0's optimizer does not exist for this
            # rank's optimizer
            missing_keys.append(r0_optim_state_key)
            continue
        param_key = optim_state_key_to_param_key[r0_optim_state_key]
        if isinstance(param_key, int):
            if not (param_key >= 0 and param_key < len(param_key_to_param)):
                raise AssertionError("Check the `param_key_to_param` construction")
    # We cannot use FSDPState.compute_device as this API is a global view.
    device = _get_pg_default_device(group)
    num_missing = torch.tensor([len(missing_keys)], dtype=torch.int32, device=device)
    dist.all_reduce(num_missing, group=group)
    if num_missing.item() > 0:
        obj_list = [None for _ in range(dist.get_world_size(group))]
        dist.all_gather_object(obj_list, missing_keys, group=group)
        error_msg = (
            "FSDP currently requires each rank to have at least the "
            "optimizer states needed by rank 0's optimizer but some ranks "
            "are missing some of those states"
        )
        for rank, keys in enumerate(obj_list):
            keys = cast(list[_OptimStateKey], keys)
            if len(keys) > 0:
                error_msg += (
                    f"\nRank {rank} is missing states for the parameters: "
                    f"{[key.unflat_param_names for key in keys]}"
                )
        raise RuntimeError(error_msg)