def _simulate_comms_compute(
    pipeline_order, stage_to_rank: Callable[[int], int], num_stages: int
):
    """This function dry-run simulates the actions in the schedule from the perspective of all ranks, and flags
    any deadlocks caused by missing or misordered communications.  It also simulates any bubbles in time where a rank
    can not execute any action due to waiting for unmet dependencies.  The total number of simulator steps can be used
    as a metric for unit tests involving IR optimization passes as reordering and merging of IR can reduce the number
    of simulated steps.

    The simulation is not high-fidelity and does not model overlapping of compute and communication, or cuda streams.
    Future work may be to enhance this and model the compute time, comms overlap, and even memory.
    """
    pipeline_order = {
        rank: [a for a in pipeline_order[rank] if a is not None]
        for rank in sorted(pipeline_order)
    }
    _schedule: dict[int, list[_Action | None]] = {
        rank: [] for rank in sorted(pipeline_order)
    }

    _prev_ops_rank: dict[int, set[_Action]] = {rank: set() for rank in _schedule}

    def add_to_schedule(rank: int, action: _Action | None):
        _schedule[rank].append(action)
        if action is not None:
            _prev_ops_rank[rank].add(action)

    def _ready_to_schedule(action: _Action | None) -> bool:
        if action is None:
            return True

        stage_idx = action.stage_index
        prev_ops = _prev_ops_rank[stage_to_rank(stage_idx)]
        if action.computation_type == F:
            if action.stage_index == 0:
                return True
            elif (
                _Action(action.stage_index, RECV_F, action.microbatch_index) in prev_ops
            ):
                return True
            elif (
                _Action(action.stage_index - 1, F, action.microbatch_index) in prev_ops
            ):
                return True
            return False
        elif action.computation_type in (BACKWARD_INPUT, FULL_BACKWARD):
            if action.stage_index == num_stages - 1:
                return True
            if _Action(action.stage_index, RECV_B, action.microbatch_index) in prev_ops:
                return True
            if (
                _Action(action.stage_index + 1, BACKWARD_INPUT, action.microbatch_index)
                in prev_ops
            ):
                return True
            if (
                _Action(action.stage_index + 1, FULL_BACKWARD, action.microbatch_index)
                in prev_ops
            ):
                return True
            return False
        elif action.computation_type == BACKWARD_WEIGHT:
            return True
        elif action.computation_type == SEND_F:
            expected_f = _Action(action.stage_index, F, action.microbatch_index)
            return expected_f in prev_ops
        elif action.computation_type == RECV_F:
            peer_stage_idx = stage_idx - 1
            expected_send = _Action(peer_stage_idx, SEND_F, action.microbatch_index)
            return expected_send in _prev_ops_rank[stage_to_rank(peer_stage_idx)]
        elif action.computation_type == SEND_B:
            expected_b = _Action(
                action.stage_index, BACKWARD_INPUT, action.microbatch_index
            )
            expected_bw = _Action(
                action.stage_index, FULL_BACKWARD, action.microbatch_index
            )
            return expected_b in prev_ops or expected_bw in prev_ops
        elif action.computation_type == RECV_B:
            peer_stage_idx = stage_idx + 1
            expected_send = _Action(peer_stage_idx, SEND_B, action.microbatch_index)
            return expected_send in _prev_ops_rank[stage_to_rank(peer_stage_idx)]
        else:
            raise ValueError(f"Unsupported action type {action}")

    while pipeline_order:
        progress = False
        for rank in sorted(pipeline_order):
            if len(pipeline_order[rank]) == 0:
                continue

            action = pipeline_order[rank][0]
            if _ready_to_schedule(action):
                if action is not None:
                    add_to_schedule(rank, action)
                pipeline_order[rank].pop(0)
                progress = True
            else:
                add_to_schedule(rank, None)

        for i in sorted(pipeline_order, reverse=True):
            if len(pipeline_order[i]) == 0:
                del pipeline_order[i]

        # hacky, but do a second pass to replace any 'none' at this timestep with a real action, if it got unblocked
        # by one of the later ranks
        for rank in sorted(pipeline_order):
            if len(pipeline_order[rank]) == 0:
                continue

            if _schedule[rank][-1] is not None:
                continue

            action = pipeline_order[rank][0]
            if _ready_to_schedule(action):
                if action is not None:
                    _schedule[rank][-1] = action
                    _prev_ops_rank[rank].add(action)
                pipeline_order[rank].pop(0)

        for i in sorted(pipeline_order, reverse=True):
            if len(pipeline_order[i]) == 0:
                del pipeline_order[i]

        if not progress:
            print("WIP comms schedule:\n", _format_pipeline_order(_schedule))
            for rank in pipeline_order:
                print(f"{rank=} next action= {pipeline_order[rank][0]}")
            raise ValueError("Schedule is not progressing")

    return _schedule