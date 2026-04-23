def generator_state(state: dict[str, str] = Depends(get_state)):
    state["/sync"] = "generator started"
    yield state["/sync"]
    state["/sync"] = "generator completed"