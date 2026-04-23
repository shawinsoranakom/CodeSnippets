def _validate_schedule(
    actions: dict[int, list[_Action | None]],
    pp_group_size: int,
    num_stages: int,
    num_microbatches: int,
) -> dict[int, int]:
    if not (len(actions) == pp_group_size):
        raise AssertionError(
            f"Schedule has incorrect number of ranks - expected {pp_group_size}, actual {len(actions)}"
        )
    for rank in range(pp_group_size):
        if rank not in actions:
            raise AssertionError(f"Schedule is missing actions for rank {rank}")

    # We will count all the actions per stage and ensure they happen in a valid order
    # (e.g. F before (B, I) before W for a given microbatch)
    stage_actions: dict[int, dict[_ComputationType, set]] = {
        stage_id: {
            F: set(),
            B: set(),
            I: set(),
            W: set(),
        }
        for stage_id in range(num_stages)
    }
    stage_index_to_rank_mapping = {}

    def _process_action(action: _Action, rank: int, step: int):
        """Process a single action and update stage_actions and stage_index_to_rank_mapping"""
        s_id = action.stage_index
        ctype = action.computation_type
        mb_id = action.microbatch_index

        if ctype == F:
            stage_actions[s_id][F].add(mb_id)
        elif ctype == B:
            if mb_id not in stage_actions[s_id][F]:
                error_msg = (
                    f"Rank {rank}, step {step}: Running Full Backward for stage {s_id}, "
                    f"microbatch {mb_id} without first running Forward"
                )
                formatted_schedule = _format_pipeline_order(
                    actions, error_step_number=step
                )
                full_error_msg = (
                    f"{error_msg}\n\nFull pipeline schedule:\n{formatted_schedule}"
                )
                raise AssertionError(full_error_msg)
            stage_actions[s_id][B].add(mb_id)
        elif ctype == I:
            if mb_id not in stage_actions[s_id][F]:
                error_msg = (
                    f"Rank {rank}, step {step}: Running Backward Input for stage {s_id}, "
                    f"microbatch {mb_id} without first running Forward"
                )
                formatted_schedule = _format_pipeline_order(
                    actions, error_step_number=step
                )
                full_error_msg = (
                    f"{error_msg}\n\nFull pipeline schedule:\n{formatted_schedule}"
                )
                raise AssertionError(full_error_msg)
            stage_actions[s_id][I].add(mb_id)
        elif ctype == W:
            if mb_id not in stage_actions[s_id][I]:
                error_msg = (
                    f"Rank {rank}, step {step}: Running Backward Weight for stage {s_id}, "
                    f"microbatch {mb_id} without first running Backward Input"
                )
                formatted_schedule = _format_pipeline_order(
                    actions, error_step_number=step
                )
                full_error_msg = (
                    f"{error_msg}\n\nFull pipeline schedule:\n{formatted_schedule}"
                )
                raise AssertionError(full_error_msg)
            stage_actions[s_id][W].add(mb_id)

        if s_id not in stage_index_to_rank_mapping:
            stage_index_to_rank_mapping[s_id] = rank
        else:
            existing_rank = stage_index_to_rank_mapping[s_id]
            if not (rank == existing_rank):
                raise AssertionError(
                    f"Rank {rank}, step {step}: Stage {s_id} is assigned to both rank {rank} and rank {existing_rank}"
                )

    for rank in actions:
        for step, action in enumerate(actions[rank]):
            if action is None:
                continue
            if not isinstance(action, _Action):
                raise AssertionError(
                    f"Rank {rank}, step {step}: Got an invalid action: {action}, expected instance of _Action"
                )

            # Check if action has sub_actions
            if action.sub_actions is not None:
                # Process each sub_action instead of the main action
                for sub_action in action.sub_actions:
                    _process_action(sub_action, rank, step)
            else:
                # Process the main action normally
                _process_action(action, rank, step)

    for s_id in stage_actions:
        f_mb = len(stage_actions[s_id][F])
        b_mb = len(stage_actions[s_id][B])
        i_mb = len(stage_actions[s_id][I])
        w_mb = len(stage_actions[s_id][W])

        if not (f_mb == num_microbatches):
            raise AssertionError(
                f"Got {f_mb} {F} microbatches for stage {s_id}, expected {num_microbatches}"
            )

        if not (i_mb == w_mb):
            raise AssertionError(
                f"Invalid backward microbatches for stage {s_id}: I and W must have equal counts, \
            but got I={i_mb}, W={w_mb}"
            )

        if not (b_mb + (i_mb + w_mb) // 2 == num_microbatches):
            raise AssertionError(
                f"Invalid backward microbatches for stage {s_id}: expected {num_microbatches} total backwards, \
            but got B={b_mb}, I={i_mb}, W={w_mb}"
            )
    return stage_index_to_rank_mapping