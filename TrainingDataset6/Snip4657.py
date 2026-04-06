def test_uvicorn_run_is_not_called_on_import():
    if sys.modules.get(MOD_NAME):
        del sys.modules[MOD_NAME]  # pragma: no cover
    with unittest.mock.patch("uvicorn.run") as uvicorn_run_mock:
        importlib.import_module(MOD_NAME)
    uvicorn_run_mock.assert_not_called()