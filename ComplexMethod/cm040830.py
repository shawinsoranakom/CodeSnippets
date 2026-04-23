def find_state(state_name: str, states: dict[str, CommonStateField]) -> CommonStateField | None:
    if state_name in states:
        return states[state_name]

    for state in states.values():
        if isinstance(state, StateMap):
            found_state = find_state(state_name, state.iteration_component._states.states)
            if found_state:
                return found_state
        elif isinstance(state, StateParallel):
            for program in state.branches.programs:
                found_state = find_state(state_name, program.states.states)
                if found_state:
                    return found_state