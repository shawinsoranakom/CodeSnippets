def get_client(request: pytest.FixtureRequest):
    clear_sqlmodel()
    # TODO: remove when updating SQL tutorial to use new lifespan API
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        mod = importlib.import_module(f"docs_src.sql_databases.{request.param}")
        clear_sqlmodel()
        importlib.reload(mod)
    mod.sqlite_url = "sqlite://"
    mod.engine = create_engine(
        mod.sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    with TestClient(mod.app) as c:
        yield c
    # Clean up connection explicitly to avoid resource warning
    mod.engine.dispose()