def test_get_new_command(output):
    assert (get_new_command(Command('git tag alert', output))
            == "git tag --force alert")