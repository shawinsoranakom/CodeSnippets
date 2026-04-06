def test_match(command):
    assert match(Command('yum {}'.format(command), yum_invalid_op_text.format(command)))