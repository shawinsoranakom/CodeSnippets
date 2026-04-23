def test_ipython_file_editor_permissions_as_openhands(temp_dir, runtime_cls):
    """Test file editor permission behavior when running as different users."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands=True)

    # Create a file owned by root with restricted permissions
    action = CmdRunAction(
        command='sudo touch /root/test.txt && sudo chmod 600 /root/test.txt'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Try to view the file as openhands user - should fail with permission denied
    test_code = "print(file_editor(command='view', path='/root/test.txt'))"
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to edit the file as openhands user - should fail with permission denied
    test_code = "print(file_editor(command='str_replace', path='/root/test.txt', old_str='', new_str='test'))"
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to create a file in root directory - should fail with permission denied
    test_code = (
        "print(file_editor(command='create', path='/root/new.txt', file_text='test'))"
    )
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to use file editor in openhands sandbox directory - should work
    test_code = """
# Create file
print(file_editor(command='create', path='/workspace/test.txt', file_text='Line 1\\nLine 2\\nLine 3'))

# View file
print(file_editor(command='view', path='/workspace/test.txt'))

# Edit file
print(file_editor(command='str_replace', path='/workspace/test.txt', old_str='Line 2', new_str='New Line 2'))

# Undo edit
print(file_editor(command='undo_edit', path='/workspace/test.txt'))
"""
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'File created successfully' in obs.content
    assert 'Line 1' in obs.content
    assert 'Line 2' in obs.content
    assert 'Line 3' in obs.content
    assert 'New Line 2' in obs.content
    assert 'Last edit to' in obs.content
    assert 'undone successfully' in obs.content

    # Clean up
    action = CmdRunAction(command='rm -f /workspace/test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='sudo rm -f /root/test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)