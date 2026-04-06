def acquire_session() -> Generator[Session, None, None]:
    session = Session()
    try:
        yield session
    finally:
        session.open = False