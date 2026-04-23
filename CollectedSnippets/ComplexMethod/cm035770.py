def test_ps1_metadata_missing_fields():
    """Test handling of missing fields in PS1 metadata"""
    # Test with only required fields
    minimal_data = {'exit_code': 0, 'pid': 123}
    ps1_str = f"""###PS1JSON###
{json.dumps(minimal_data)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username is None
    assert metadata.hostname is None
    assert metadata.working_dir is None
    assert metadata.py_interpreter_path is None

    # Test with missing exit_code but valid pid
    no_exit_code = {'pid': 123, 'username': 'test'}
    ps1_str = f"""###PS1JSON###
{json.dumps(no_exit_code)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == -1  # default value
    assert metadata.pid == 123
    assert metadata.username == 'test'