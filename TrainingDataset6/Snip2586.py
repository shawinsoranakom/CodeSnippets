def get_named_regular_func_session(session: SessionFuncDep) -> Any:
    named_session = NamedSession(name="named")
    return named_session, session