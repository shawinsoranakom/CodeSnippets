async def dep_session() -> Any:
    s = Session()
    yield s
    s.open = False
    global_state = global_context.get()
    global_state["session_closed"] = True