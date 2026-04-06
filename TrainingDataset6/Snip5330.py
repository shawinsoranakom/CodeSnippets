def get_test_module(request: pytest.FixtureRequest) -> ModuleType:
    mod: ModuleType = importlib.import_module(
        f"docs_src.dependency_testing.{request.param}"
    )
    return mod