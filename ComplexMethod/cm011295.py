def _merge_bw(
    compute_actions: list[_Action | None],
) -> list[_Action]:
    """Given a basic schedule involving only compute actions (F,I,W), merge adjacent I and W ops into B ops.
    (note: I = BACKWARD_INPUT, W = BACKWARD_WEIGHT, B = FULL_BACKWARD)

    B refers to running the whole backward (not separating grad_input and grad_weight), which can be more efficient
    in some cases.
    """
    merged_actions = []
    while compute_actions:
        action = compute_actions.pop(0)
        if action is None:
            continue

        # Remove any None actions and find the next non-None action
        while len(compute_actions) and compute_actions[0] is None:
            compute_actions.pop(0)

        # Get the next action if it exists
        next_action = compute_actions[0] if len(compute_actions) > 0 else None

        if (
            action.computation_type == BACKWARD_INPUT
            and next_action is not None
            and next_action.computation_type == BACKWARD_WEIGHT
            and action.stage_index == next_action.stage_index
            and action.microbatch_index == next_action.microbatch_index
        ):
            merged_actions.append(
                _Action(action.stage_index, FULL_BACKWARD, action.microbatch_index)
            )
            compute_actions.pop(0)
        else:
            merged_actions.append(action)
    return merged_actions