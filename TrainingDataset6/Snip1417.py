def test_match_goenv_output_quote():
    """test goenv's specific output with quotes (')"""
    assert match(Command('goenv list', output="goenv: no such command 'list'"))