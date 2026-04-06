def broken_dep_session() -> Any:
    with acquire_session() as s:
        s.open = False
        yield s