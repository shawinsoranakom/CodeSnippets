def get_data(session: SessionDep) -> Any:
    data = list(session)
    return data