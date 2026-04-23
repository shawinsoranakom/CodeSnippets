def from_str(action_string: str):
        """
        Reverse of __repr__

        String should be formatted as [stage][action type][(microbatch)]
            e.g. `2F0`, `1UNSHARD`, `3SEND_F1`
        """
        action_string = action_string.strip()
        if action_string == "":
            return None

        # Check for sub_actions format: [sub_action1;sub_action2;...]ComputationType
        if action_string.startswith("(") and ")" in action_string:
            # Find the closing bracket to separate sub_actions from computation type
            bracket_end = action_string.find(")")
            sub_part = action_string[
                1:bracket_end
            ]  # Remove '[' and get content before ']'
            computation_type_part = action_string[
                bracket_end + 1 :
            ]  # Get part after ']'

            # Parse sub_actions
            sub_actions = []
            if sub_part.strip():
                for sub_str in sub_part.split(";"):
                    sub_action = _Action.from_str(sub_str.strip())
                    if sub_action is not None:
                        sub_actions.append(sub_action)

            # For sub_actions format, we create an action with just the computation type
            # The stage_index and microbatch_index are not meaningful for the container action
            return _Action(
                stage_index=-1,  # Placeholder, not meaningful for sub_actions container
                computation_type=_ComputationType.from_str(computation_type_part),
                microbatch_index=None,
                sub_actions=tuple(sub_actions) if sub_actions else None,
            )

        # Handle regular single action format
        if match := _action_regex.match(action_string):
            stage_index, computation_type, microbatch_index = match.groups()
            return _Action(
                int(stage_index),
                _ComputationType.from_str(computation_type),
                int(microbatch_index) if len(microbatch_index) else None,
            )
        elif action_string == "":
            return None
        raise RuntimeError(
            f"Invalid action string: {action_string}, should be formatted as [stage][action type][(microbatch)] e.g. 2F0"
        )