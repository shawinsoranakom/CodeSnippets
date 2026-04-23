def add_schedule_op_spacing(
    schedule: list[list[_Action | None]],
) -> list[list[_Action | None]]:
    """
    Add spacing to the schedule based on dependencies between ranks.

    Before adding an operation to the list, this function checks if there are
    dependencies from other ranks. If there are dependencies (other ranks have
    not finished processing the required microbatch), it adds None instead.

    For example, Forward microbatch 0 on rank 1 depends on rank 0 processing
    Forward microbatch 0 first.

    Args:
        schedule: The original schedule as a list of lists where each inner list
                 represents a rank and each element represents an action.

    Returns:
        A new schedule with proper spacing based on dependencies.
    """
    if not schedule:
        return schedule

    num_stages = (
        max(
            action.stage_index
            for rank_actions in schedule
            for action in rank_actions
            if action is not None
        )
        + 1
    )

    num_ranks = len(schedule)
    spaced_schedule: list[list[_Action | None]] = [[] for _ in range(num_ranks)]
    rank_ops = [collections.deque(ops) for ops in schedule]

    # Track completion times: (stage_index, action_type, microbatch_index) -> completion_time
    scheduled_ops: dict[OpKey, int] = {}

    def is_dependency_ready(dependency_key: OpKey, timestep: int) -> bool:
        """Check if a dependency operation has completed by the given timestep."""
        return (
            dependency_key in scheduled_ops
            and timestep >= scheduled_ops[dependency_key]
        )

    def get_dependencies(action: _Action) -> list[OpKey]:
        """Get the list of dependencies for an action."""
        stage_idx = action.stage_index
        comp_type = action.computation_type
        mb_idx = action.microbatch_index

        # Ensure mb_idx is not None for dependency tracking
        if mb_idx is None:
            raise AssertionError(f"Action {action} has None microbatch_index")

        # First stage forward has no dependencies
        if stage_idx == 0 and comp_type == _ComputationType.FORWARD:
            return []

        # Last stage backward depends on forward from previous stage
        if stage_idx == num_stages - 1 and comp_type in (
            _ComputationType.FULL_BACKWARD,
            _ComputationType.BACKWARD_INPUT,
        ):
            return [OpKey(stage_idx - 1, _ComputationType.FORWARD, mb_idx)]

        # Forward depends on previous stage forward
        if comp_type == _ComputationType.FORWARD:
            return [OpKey(stage_idx - 1, _ComputationType.FORWARD, mb_idx)]

        # Backward depends on next stage backward
        if comp_type in (
            _ComputationType.FULL_BACKWARD,
            _ComputationType.BACKWARD_INPUT,
        ):
            return [
                OpKey(stage_idx + 1, _ComputationType.FULL_BACKWARD, mb_idx),
                OpKey(stage_idx + 1, _ComputationType.BACKWARD_INPUT, mb_idx),
            ]

        # Weight backward depends on input backward
        if comp_type == _ComputationType.BACKWARD_WEIGHT:
            return [OpKey(stage_idx, _ComputationType.BACKWARD_INPUT, mb_idx)]

        raise RuntimeError(f"Unknown computation type: {comp_type}")

    def is_action_ready(action: _Action, timestep: int) -> bool:
        """Check if an action is ready to be scheduled at the given timestep."""
        # For OR dependencies (like backward), check if any dependency is satisfied
        if action.computation_type in (
            _ComputationType.FULL_BACKWARD,
            _ComputationType.BACKWARD_INPUT,
            _ComputationType.BACKWARD_WEIGHT,
        ):
            dependencies = get_dependencies(action)
            return any(is_dependency_ready(dep, timestep) for dep in dependencies)
        # For AND dependencies, all must be satisfied
        elif action.computation_type == _ComputationType.FORWARD:
            dependencies = get_dependencies(action)
            return all(is_dependency_ready(dep, timestep) for dep in dependencies)
        elif action.computation_type == _ComputationType.OVERLAP_F_B:
            if action.sub_actions is None:
                raise AssertionError(
                    f"OVERLAP_F_B action {action} has None sub_actions"
                )
            dep_list: list[bool] = []
            for sub_action in action.sub_actions:
                dep_list.append(is_action_ready(sub_action, timestep))
            return all(dep_list)
        else:
            raise RuntimeError(f"Unknown computation type: {action.computation_type}")

    def schedule_action(action: _Action, rank: int, timestep: int) -> int:
        """Schedule an action and return completion time."""
        spaced_schedule[rank].append(action)
        comp_type = action.computation_type
        comp_time = action_type_to_color_mapping[comp_type].width
        completion_time = timestep + comp_time

        if comp_type == _ComputationType.OVERLAP_F_B:
            # For overlap actions, schedule each sub-action with cumulative timing
            if action.sub_actions is None:
                raise AssertionError(
                    f"OVERLAP_F_B action {action} has None sub_actions"
                )
            cumulative_time = 0
            for sub_action in action.sub_actions:
                if sub_action.microbatch_index is None:
                    raise AssertionError(
                        f"Sub-action {sub_action} has None microbatch_index"
                    )
                sub_comp_time = action_type_to_color_mapping[
                    sub_action.computation_type
                ].width
                cumulative_time += sub_comp_time
                scheduled_ops[
                    OpKey(
                        sub_action.stage_index,
                        sub_action.computation_type,
                        sub_action.microbatch_index,
                    )
                ] = timestep + cumulative_time
        else:
            if action.microbatch_index is None:
                raise AssertionError(f"Action {action} has None microbatch_index")
            scheduled_ops[
                OpKey(action.stage_index, comp_type, action.microbatch_index)
            ] = completion_time

        return completion_time

    # Main scheduling loop
    current_timestep = 0
    timesteps_without_progress = 0
    rank_completion_times = dict.fromkeys(range(num_ranks), 0)
    while rank_ops:
        print(f"Current timestep: {current_timestep}")
        # Process all operations during timestep until we run out of ready operations
        for rank, op_queue in enumerate(rank_ops):
            if not op_queue:
                continue

            op_queue = rank_ops[rank]
            action = op_queue[0]
            print(f"Rank: {rank}, {action=}")
            if action is None:
                spaced_schedule[rank].append(None)
                op_queue.popleft()
                timesteps_without_progress = 0
            elif current_timestep >= rank_completion_times[rank] and is_action_ready(
                action, current_timestep
            ):
                rank_completion_times[rank] = schedule_action(
                    action, rank, current_timestep
                )
                op_queue.popleft()
                timesteps_without_progress = 0

        # Add None for ranks that are waiting
        for rank in range(num_ranks):
            if current_timestep >= rank_completion_times[rank]:
                spaced_schedule[rank].append(None)

        # Remove empty queues and advance timestep
        rank_ops = [op_queue for op_queue in rank_ops if op_queue]
        current_timestep += 1
        timesteps_without_progress += 1

        if timesteps_without_progress > max(
            visual.width for visual in action_type_to_color_mapping.values()
        ):
            raise RuntimeError("No progress made in scheduling - possible deadlock")

    return spaced_schedule