async def asyncgen_state(state: dict[str, str] = Depends(get_state)):
    state["/async"] = "asyncgen started"
    yield state["/async"]
    state["/async"] = "asyncgen completed"