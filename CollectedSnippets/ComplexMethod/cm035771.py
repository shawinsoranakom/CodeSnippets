def test_cmd_output_observation_properties():
    """Test CmdOutputObservation class properties"""
    # Test with successful command
    metadata = CmdOutputMetadata(exit_code=0, pid=123)
    obs = CmdOutputObservation(command='ls', content='file1\nfile2', metadata=metadata)
    assert obs.command_id == 123
    assert obs.exit_code == 0
    assert not obs.error
    assert 'exit code 0' in obs.message
    assert 'ls' in obs.message
    assert 'file1' in str(obs)
    assert 'file2' in str(obs)
    assert 'metadata' in str(obs)

    # Test with failed command
    metadata = CmdOutputMetadata(exit_code=1, pid=456)
    obs = CmdOutputObservation(command='invalid', content='error', metadata=metadata)
    assert obs.command_id == 456
    assert obs.exit_code == 1
    assert obs.error
    assert 'exit code 1' in obs.message
    assert 'invalid' in obs.message
    assert 'error' in str(obs)