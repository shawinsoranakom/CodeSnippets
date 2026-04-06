def test_not_match(lsof, command, lsof_output):
    lsof.return_value.stdout = BytesIO(lsof_output)

    assert not match(command)