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