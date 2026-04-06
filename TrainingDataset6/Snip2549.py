def dep_session() -> Any:
    s = Session()
    yield s
    s.open = False