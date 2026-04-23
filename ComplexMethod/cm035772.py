def test_ps1_metadata_empty_fields():
    """Test handling of empty fields in PS1 metadata"""
    # Test with empty strings
    empty_data = {
        'exit_code': 0,
        'pid': 123,
        'username': '',
        'hostname': '',
        'working_dir': '',
        'py_interpreter_path': '',
    }
    ps1_str = f"""###PS1JSON###
{json.dumps(empty_data)}
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(ps1_str)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username == ''
    assert metadata.hostname == ''
    assert metadata.working_dir == ''
    assert metadata.py_interpreter_path == ''

    # Test with malformed but valid JSON
    malformed_json = """###PS1JSON###
    {
        "exit_code":0,
        "pid"  :  123,
        "username":    "test"  ,
        "hostname": "host",
        "working_dir"    :"dir",
        "py_interpreter_path":"path"
    }
###PS1END###
"""
    matches = CmdOutputMetadata.matches_ps1_metadata(malformed_json)
    assert len(matches) == 1
    metadata = CmdOutputMetadata.from_ps1_match(matches[0])
    assert metadata.exit_code == 0
    assert metadata.pid == 123
    assert metadata.username == 'test'
    assert metadata.hostname == 'host'
    assert metadata.working_dir == 'dir'
    assert metadata.py_interpreter_path == 'path'