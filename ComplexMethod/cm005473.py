def gather_state_dict_for_save(
    state_dict: dict[str, torch.Tensor],
    tp_plan: dict[str, str],
    device_mesh,
    tp_size: int,
) -> dict[str, torch.Tensor]:
    """
    Gather sharded tensors to reconstruct full tensors for saving.

    This function all-gathers each sharded tensor along its shard dimension
    to reconstruct the full unsharded tensor for checkpoint saving.

    Args:
        state_dict: The model state dict with local sharded tensors
        tp_plan: The tensor parallel plan mapping layer patterns to shard styles
        device_mesh: The device mesh for distributed communication
        tp_size: The tensor parallel world size

    Returns:
        State dict with full (gathered) tensors
    """
    # Use the global mappings from ParallelInterface (can be extended by users)
    plan_to_weight_dim = ALL_PARALLEL_STYLES.plan_to_weight_dim
    plan_to_bias_dim = ALL_PARALLEL_STYLES.plan_to_bias_dim

    result = {}
    for key, tensor in state_dict.items():
        # Find the matching TP plan for this parameter
        param_name = key.rsplit(".", 1)[0] if "." in key else key
        param_type = key.rsplit(".", 1)[1] if "." in key else None
        generic_param_name = re.sub(r"\d+", "*", param_name)
        # Also check the full key for nn.Parameter (e.g., MoE experts without .weight suffix)
        generic_full_key = re.sub(r"\d+", "*", key)

        # Check if this parameter has a TP plan
        current_plan = None
        if generic_full_key in tp_plan:
            # Full key match (e.g., "model.layers.*.mlp.experts.gate_up_proj" for MoE experts)
            current_plan = tp_plan[generic_full_key]
        elif generic_param_name in tp_plan:
            current_plan = tp_plan[generic_param_name]
        elif "." in generic_param_name:
            parent_param_name = generic_param_name.rsplit(".", 1)[0]
            if parent_param_name in tp_plan:
                current_plan = tp_plan[parent_param_name]

        if current_plan is None or current_plan not in plan_to_weight_dim:
            # Not sharded, keep as-is
            result[key] = tensor
            continue

        # Determine sharding dimension based on param type
        if param_type == "bias":
            shard_dim = plan_to_bias_dim.get(current_plan)
        else:
            shard_dim = plan_to_weight_dim.get(current_plan)

        if shard_dim is None:
            # Replicated, keep as-is
            result[key] = tensor
            continue

        # Gather full tensor and handle packed weights repacking
        full_tensor = gather_full_tensor(tensor, shard_dim, device_mesh)
        if current_plan in ("packed_colwise", "packed_rowwise"):
            full_tensor = repack_weights(full_tensor, shard_dim, tp_size, 2)
        result[key] = full_tensor.contiguous()

    return result