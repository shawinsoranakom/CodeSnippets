def test_say_hi(module: ModuleType):
    with patch("builtins.print") as mock_print:
        module.say_hi("FastAPI")
        module.say_hi()

    assert mock_print.call_count == 2
    call_args = [arg.args for arg in mock_print.call_args_list]
    assert call_args == [
        ("Hey FastAPI!",),
        ("Hello World",),
    ]