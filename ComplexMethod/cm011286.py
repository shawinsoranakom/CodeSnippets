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