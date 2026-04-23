def _verify_tp_sharding(rank, model_tp, model_ref):
    """Verify TP sharding by comparing parameter shapes between TP and reference models.

    Returns:
        list: Names of sharded parameters
    """
    world_size = dist.get_world_size()
    sharded_params = []

    for (name, param), (_, param_full) in zip(model_tp.named_parameters(), model_ref.named_parameters()):
        if param.shape != param_full.shape:
            sharded_params.append(name)
            if rank == 0:
                print(f"[TP Test Debug] TP sharded: {name} - full: {param_full.shape} -> sharded: {param.shape}")

            # Verify sharding is correct
            for dim in range(param.ndim):
                if param.size(dim) != param_full.size(dim):
                    param_plan = _get_parameter_tp_plan(name, model_tp.tp_plan, is_weight=True)
                    if param_plan in ("packed_colwise",):
                        expected_size = param_full.size(dim) // world_size
                        assert param.size(dim) == expected_size, (
                            f"Packed weight {name} sharding incorrect: expected {expected_size}, got {param.size(dim)}"
                        )
                    else:
                        expected_size = (param_full.size(dim) + world_size - 1) // world_size
                        assert param.size(dim) <= expected_size, (
                            f"Weight {name} sharding incorrect: expected <= {expected_size}, got {param.size(dim)}"
                        )
                    break

    return sharded_params