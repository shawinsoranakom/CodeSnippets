def next_stage_indices(count: int, next_actions: list[_Action | None]) -> list[int]:
        """Remove duplicates (same stage, different microbatch), find next 'count' stages that will do compute."""
        seen: set[int] = set()
        ret: list[int] = []

        for a in next_actions:
            if a is not None:
                # Handle OVERLAP_F_B actions by checking their sub_actions
                if a.computation_type == OVERLAP_F_B and a.sub_actions is not None:
                    for sub_action in a.sub_actions:
                        if sub_action.stage_index not in seen:
                            seen.add(sub_action.stage_index)
                            ret.append(sub_action.stage_index)
                    if len(ret) >= count:
                        break
                else:
                    # Regular action
                    if a.stage_index not in seen:
                        seen.add(a.stage_index)
                        ret.append(a.stage_index)
                        if len(ret) == count:
                            break
        return ret