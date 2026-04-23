def _compare_save_plans(plan: SavePlan, other_plan: SavePlan) -> bool:
    """
    Compare the two Save plans and return True if they are equal.

    Args:
        plan (SavePlan): First SavePlan to compare.
        other_plan (SavePlan): Second SavePlan to compare.

    Returns:
       True if the two plans are equal, False otherwise.
    """
    if plan.usable != other_plan.usable:
        return False

    # Both the plans should have the same number of items
    if len(plan.items) != len(other_plan.items):
        return False

    # Both the plans should have the same write items.
    for plan_item, other_plan_item in zip(plan.items, other_plan.items):
        # Write item type should be same
        if plan_item.type != other_plan_item.type:
            return False

        plan_metadata_index = plan_item.index
        other_plan_metadata_index = other_plan_item.index

        # Write item metadata_index should be same
        if (
            plan_metadata_index.fqn != other_plan_metadata_index.fqn
            or plan_metadata_index.offset != other_plan_metadata_index.offset
            or plan_metadata_index.index != other_plan_metadata_index.index
        ):
            return False

        # Write item tensor_data should be present in both the write items plans, if it exists in either of them.
        tensor_data = plan_item.tensor_data
        other_tensor_data = other_plan_item.tensor_data
        if (tensor_data and not other_tensor_data) or (
            not tensor_data and other_tensor_data
        ):
            return False

        if tensor_data and other_tensor_data:
            # Write item tensor_data size should be same
            if tensor_data.size != other_tensor_data.size:
                return False

            # Write item tensor_data chunk should be present in both the write items, if it exists in either of them.
            chunk = tensor_data.chunk
            other_chunk = other_tensor_data.chunk
            if (chunk and not other_chunk) or (not chunk and other_chunk):
                return False

            # Write item tensor_data chunk offsets and sizes should be same
            if chunk and other_chunk:
                if (
                    chunk.offsets != other_chunk.offsets
                    or chunk.sizes != other_chunk.sizes
                ):
                    return False

    return True