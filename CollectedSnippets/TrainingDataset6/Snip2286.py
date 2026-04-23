def dep_session() -> Any:
    with acquire_session() as s:
        yield s