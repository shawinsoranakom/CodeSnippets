def test_get_operations(set_help):
    set_help(help_text)
    assert _get_operations() == dnf_operations