def test_uvicorn_run_called_when_run_as_main():  # Just for coverage
    if sys.modules.get(MOD_NAME):
        del sys.modules[MOD_NAME]
    with unittest.mock.patch("uvicorn.run") as uvicorn_run_mock:
        runpy.run_module(MOD_NAME, run_name="__main__")

    uvicorn_run_mock.assert_called_once_with(
        unittest.mock.ANY, host="0.0.0.0", port=8000
    )