def test_process_items(module: ModuleType):
    with patch("builtins.print") as mock_print:
        module.process_item("a")

    assert mock_print.call_count == 1
    mock_print.assert_called_with("a")