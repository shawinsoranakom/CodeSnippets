def test_run_module(module_name: str):
    with patch("builtins.print") as mock_print:
        runpy.run_module(f"docs_src.python_types.{module_name}", run_name="__main__")

    assert mock_print.call_count == 2
    call_args = [str(arg.args[0]) for arg in mock_print.call_args_list]
    assert call_args == [
        "id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]",
        "123",
    ]