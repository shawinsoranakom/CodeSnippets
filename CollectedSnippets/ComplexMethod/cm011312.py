def _add_bubbles_to_actions(self, num_stages_global):
        actions = self.pipeline_order

        def need_bubble(stage, op, microbatch, num_stages_global, seen_ops):
            if op == _ComputationType.FORWARD:
                if stage != 0 and (stage - 1, op, microbatch) not in seen_ops:
                    return True
            elif op == _ComputationType.FULL_BACKWARD:
                if stage == num_stages_global - 1:
                    return (stage, _ComputationType.FORWARD, microbatch) not in seen_ops
                return (stage + 1, op, microbatch) not in seen_ops
            return False

        seen_ops: set[tuple[int, _ComputationType, int]] = set()
        result: dict[int, list[_Action | None]] = {}
        next_pointer: dict[int, int] = {}
        bubbles_added: dict[int, int] = {}
        total_bubbles_added = 0

        for rank in range(self.pp_group_size):
            result[rank] = []
            next_pointer[rank] = 0
            bubbles_added[rank] = 0

        while True:
            should_stop = True

            temp_seen_ops: set[tuple[int, _ComputationType, int]] = set()

            for rank in range(self.pp_group_size):
                timestamp = next_pointer[rank]
                if timestamp >= len(actions[rank]):
                    continue

                should_stop = False

                if actions[rank][timestamp] is not None:
                    temp_action = actions[rank][timestamp]
                    if temp_action is None:
                        raise AssertionError(
                            f"Expected temp_action to be not None, got {type(temp_action)}"
                        )
                    stage_index, op, microbatch, _ = temp_action
                    if not need_bubble(
                        stage_index, op, microbatch, num_stages_global, seen_ops
                    ):
                        result[rank].append(actions[rank][timestamp])
                        if microbatch is not None:
                            temp_seen_ops.add((stage_index, op, microbatch))
                        next_pointer[rank] += 1
                    else:
                        result[rank].append(None)
                        bubbles_added[rank] += 1
                else:
                    next_pointer[rank] += 1
                    result[rank].append(None)

            seen_ops.update(temp_seen_ops)
            if should_stop:
                break

        if total_bubbles_added > 0:
            logger.warning(
                "Non zero bubbles added: total_bubbles_added=%s bubbles_added=%s",
                total_bubbles_added,
                bubbles_added,
            )
        return result