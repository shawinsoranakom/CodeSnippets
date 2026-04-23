def _add_send_recv(
    compute_actions: dict[int, list[_Action]],
    stage_to_rank: Callable[[int], int],
    num_stages: int,
) -> dict[int, list[_Action]]:
    """
    Transforms a compute-only schedule into a complete schedule with communication actions.

    For actions with sub-actions (OVERLAP_F_B) we ensure that all the subactions have been
    computed and the communication is ready
    """
    comm_actions: dict[int, list[_Action]] = {rank: [] for rank in compute_actions}
    prev_actions: dict[int, set[_Action]] = {rank: set() for rank in compute_actions}

    def _has_comms(action: _Action) -> bool:
        if action.computation_type == F:
            return action.stage_index != num_stages - 1 and stage_to_rank(
                action.stage_index + 1
            ) != stage_to_rank(action.stage_index)
        elif action.computation_type in (BACKWARD_INPUT, FULL_BACKWARD):
            return action.stage_index != 0 and stage_to_rank(
                action.stage_index - 1
            ) != stage_to_rank(action.stage_index)
        return False

    def _get_comms(action: _Action) -> tuple[_Action, _Action]:
        if not _has_comms(action):
            raise AssertionError(f"{action} is not a valid comm action")
        stage_idx = action.stage_index
        ctype = action.computation_type
        mb_idx = action.microbatch_index
        send = _Action(stage_idx, SEND_F if ctype == F else SEND_B, mb_idx)
        recv_stage_idx = stage_idx + 1 if ctype == F else stage_idx - 1
        recv = _Action(recv_stage_idx, RECV_F if ctype == F else RECV_B, mb_idx)
        return send, recv

    def _ready_to_schedule(action: _Action | None, prev_actions: set[_Action]) -> bool:
        """We don't put our own recv ops in the schedule, we let a sender on another rank put our recv ops in place.
        This helps ensure a sane (non-hanging) ordering of sends and recvs.
        But it also means we might not be able to schedule our next compute action yet.
        """
        if action is None:
            return True
        elif action.computation_type == F and action.stage_index != 0:
            if (
                _Action(action.stage_index, RECV_F, action.microbatch_index)
                in prev_actions
            ):
                return True
            elif (
                _Action(action.stage_index - 1, F, action.microbatch_index)
                in prev_actions
            ):
                return True
            return False
        elif (
            action.computation_type in (BACKWARD_INPUT, FULL_BACKWARD)
            and action.stage_index != num_stages - 1
        ):
            if (
                _Action(action.stage_index, RECV_B, action.microbatch_index)
                in prev_actions
            ):
                return True
            elif (
                _Action(action.stage_index + 1, BACKWARD_INPUT, action.microbatch_index)
                in prev_actions
            ):
                return True
            elif (
                _Action(action.stage_index + 1, FULL_BACKWARD, action.microbatch_index)
                in prev_actions
            ):
                return True
            return False
        else:
            return True

    while compute_actions:
        progress = False
        # go in order of ranks even if dict keys aren't ordered
        for rank in sorted(compute_actions):
            if not (len(compute_actions[rank]) > 0):
                raise AssertionError(f"{rank=}, {len(compute_actions[rank])=}")
            action = compute_actions[rank][0]
            # handle case where parent action (e.g. OVERLAP_F_B) can be comprised of subactions
            if action is not None and action.sub_actions is not None:
                all_actions = action.sub_actions
            else:
                all_actions = (action,)

            if not all(_ready_to_schedule(a, prev_actions[rank]) for a in all_actions):
                continue

            # The action's dependencies are satisfied, so add to schedule
            if action is not None:
                comm_actions[rank].append(action)
                for a in all_actions:
                    prev_actions[rank].add(a)
                    if _has_comms(a):
                        send, recv = _get_comms(a)
                        # TODO we can avoid send/recv if the 2 stages are on the same rank.
                        # should we avoid that in the runtime or here?
                        comm_actions[rank].append(send)
                        prev_actions[rank].add(send)
                        comm_actions[stage_to_rank(recv.stage_index)].append(recv)
                        prev_actions[stage_to_rank(recv.stage_index)].add(recv)

            compute_actions[rank].pop(0)
            if len(compute_actions[rank]) == 0:
                del compute_actions[rank]
            progress = True
        if not progress:
            raise AssertionError(
                "Malformed compute schedule, can't schedule sends/recvs"
            )
    return comm_actions