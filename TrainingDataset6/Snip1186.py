def test_match():
    assert match(Command('git clone git clone foo', output_clean))