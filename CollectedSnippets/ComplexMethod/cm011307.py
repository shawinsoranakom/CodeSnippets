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