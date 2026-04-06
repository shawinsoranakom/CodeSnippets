def test_run_module(module_name: str):
    with patch("builtins.print") as mock_print:
        runpy.run_module(f"docs_src.python_types.{module_name}", run_name="__main__")

    mock_print.assert_called_with("John Doe")