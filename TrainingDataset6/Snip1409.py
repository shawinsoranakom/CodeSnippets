def test_not_match(run_script, command, run_script_out):
    run_script.stdout = BytesIO(run_script_out)
    assert not match(command)