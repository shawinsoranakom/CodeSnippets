def get_named_func_session(session: SessionFuncDep) -> Any:
    named_session = NamedSession(name="named")
    yield named_session, session
    named_session.open = False
    global_state = global_context.get()
    global_state["named_func_session_closed"] = True