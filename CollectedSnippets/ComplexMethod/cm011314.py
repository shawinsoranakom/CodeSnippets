def _calculate_single_rank_operations(self, rank) -> list[_Action | None]:
        actions: list[_Action | None] = []
        counters: dict[
            tuple[int, _ComputationType], int
        ] = {}  # (stage_index, computation_type) -> mb_index
        weight_queue = []  # Queue of (stage_index, mb_index) for pending weight actions

        num_ranks = self.pp_group_size
        num_chunks = self._n_microbatches

        rank_to_stages = generate_rank_to_stage_mapping(
            num_ranks, num_ranks * 2, style="v"
        )
        stage0_index, stage1_index = rank_to_stages[rank]

        def increment_backward_counts(stage_index: int):
            """Helper method to increment BACKWARD_INPUT and BACKWARD_WEIGHT counters when FULL_BACKWARD is used."""
            input_key = (stage_index, BACKWARD_INPUT)
            weight_key = (stage_index, BACKWARD_WEIGHT)
            counters[input_key] = counters.get(input_key, 0) + 1
            counters[weight_key] = counters.get(weight_key, 0) + 1

        def add_overlap_f_b(
            actions: list,
            forward_stage: int,
            backward_stage: int,
        ):
            """Helper method to add an overlapped forward+backward action which tracks microbatch index."""
            # Create new overlapped forward+backward action with sub_actions
            forward_key = (forward_stage, FORWARD)
            backward_key = (backward_stage, BACKWARD_INPUT)

            forward_mb = counters.get(forward_key, 0)
            backward_mb = counters.get(backward_key, 0)

            sub_actions = (
                _Action(forward_stage, FORWARD, forward_mb),
                _Action(backward_stage, FULL_BACKWARD, backward_mb),
            )
            actions.append(_Action(-1, OVERLAP_F_B, None, sub_actions))

            # Update counters for sub_actions
            counters[forward_key] = forward_mb + 1
            increment_backward_counts(backward_stage)

        def add_action(
            actions: list,
            stage_index: int,
            computation_type: _ComputationType,
        ):
            # Regular single action, for FULL_BACKWARD we only use the BACKWARD_INPUT counter
            key = (
                (stage_index, computation_type)
                if computation_type != FULL_BACKWARD
                else (stage_index, BACKWARD_INPUT)
            )
            mb_index = counters.get(key, 0)
            actions.append(_Action(stage_index, computation_type, mb_index))

            # If FULL_BACKWARD is used, just increment the separate BACKWARD_INPUT and BACKWARD_WEIGHT counters
            if computation_type == FULL_BACKWARD:
                increment_backward_counts(stage_index)
            else:
                # If BACKWARD_INPUT is updated, add corresponding weight action to queue
                if computation_type == BACKWARD_INPUT:
                    # Add weight action to queue for later processing
                    weight_queue.append((stage_index, mb_index))
                counters[key] = mb_index + 1

        def add_weight_action_if_pending(actions: list):
            """Helper method to add a weight action from the queue."""
            if not weight_queue:
                return  # No pending weight actions, skip
            # Pop the oldest weight action from the queue
            actual_stage_index, weight_mb_index = weight_queue.pop(0)
            actions.append(
                _Action(
                    actual_stage_index,
                    BACKWARD_WEIGHT,
                    weight_mb_index,
                )
            )
            # Update the counter for the actual stage that was processed
            weight_key = (actual_stage_index, BACKWARD_WEIGHT)
            counters[weight_key] = counters.get(weight_key, 0) + 1

        # Step 1: F0
        step_1 = (num_ranks - rank - 1) * 2
        for _ in range(step_1):
            add_action(actions, stage0_index, FORWARD)

        # Step 2: F0F1
        step_2 = rank + 1
        for _ in range(step_2):
            add_action(actions, stage0_index, FORWARD)
            add_action(actions, stage1_index, FORWARD)

        # Step 3: I1W1F1 (Use zero bubble)
        step_3 = num_ranks - rank - 1
        for _ in range(step_3):
            add_action(actions, stage1_index, BACKWARD_INPUT)
            add_weight_action_if_pending(actions)
            add_action(actions, stage1_index, FORWARD)

        # Step 4 (Main step): F0B1-F1B0 (combined, overlapped forward+backward)
        step_4 = num_chunks - num_ranks * 2 + rank + 1
        for i in range(step_4):
            if i == 0 and rank == num_ranks - 1:
                # NOTE: We don't overlap these two chunks to further reduce bubble size.
                add_action(actions, stage0_index, FORWARD)
                add_action(actions, stage1_index, FULL_BACKWARD)
            else:
                add_overlap_f_b(
                    actions,
                    forward_stage=stage0_index,
                    backward_stage=stage1_index,
                )
            add_overlap_f_b(
                actions,
                forward_stage=stage1_index,
                backward_stage=stage0_index,
            )

        # Step 5: B1-F1B0
        step_5 = num_ranks - rank - 1
        for _ in range(step_5):
            add_action(actions, stage1_index, FULL_BACKWARD)
            add_overlap_f_b(
                actions,
                forward_stage=stage1_index,
                backward_stage=stage0_index,
            )

        # Step 6: B1B0 (The second half of the chunks use zero bubble)
        step_6 = rank + 1
        enable_zb = False
        for i in range(step_6):
            if i == step_6 // 2 and rank % 2 == 1:
                enable_zb = True
            comp_type = BACKWARD_INPUT if enable_zb else FULL_BACKWARD
            add_action(actions, stage1_index, comp_type)
            if i == step_6 // 2 and rank % 2 == 0:
                enable_zb = True
            comp_type = BACKWARD_INPUT if enable_zb else FULL_BACKWARD
            add_action(actions, stage0_index, comp_type)

        # Step 7: W0B0
        step_7 = num_ranks - rank - 1
        for _ in range(step_7):
            add_weight_action_if_pending(actions)
            comp_type = BACKWARD_INPUT if enable_zb else FULL_BACKWARD
            add_action(actions, stage0_index, comp_type)

        # Step 8: W0
        step_8 = rank + 1
        for _ in range(step_8):
            add_weight_action_if_pending(actions)

        return actions