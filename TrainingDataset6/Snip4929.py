def test_process_items():
    with patch("builtins.print") as mock_print:
        process_items(["item_a", "item_b", "item_c"])

    assert mock_print.call_count == 3
    call_args = [arg.args for arg in mock_print.call_args_list]
    assert call_args == [
        ("item_a",),
        ("item_b",),
        ("item_c",),
    ]