async def test_clone_or_init_repo_with_branch(temp_dir, monkeypatch):
    """Test cloning a repository with a specified branch"""
    config = OpenHandsConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    runtime = MockRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITHUB)
    result = await runtime.clone_or_init_repo(None, 'owner/repo', 'feature-branch')

    # Verify that git clone, checkout, and remote update were called
    assert len(runtime.run_action_calls) == 3  # clone, checkout, set-url
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)
    assert isinstance(runtime.run_action_calls[1], CmdRunAction)
    assert isinstance(runtime.run_action_calls[2], CmdRunAction)

    # Check that the first command is the git clone
    clone_cmd = runtime.run_action_calls[0].command
    expected_repo_path = str(runtime.workspace_root / 'repo')
    assert 'git clone https://github.com/owner/repo.git' in clone_cmd
    assert expected_repo_path in clone_cmd

    # Check that the second command contains the correct branch checkout
    checkout_cmd = runtime.run_action_calls[1].command
    assert f'cd {expected_repo_path}' in checkout_cmd
    assert 'git checkout feature-branch' in checkout_cmd
    set_url_cmd = runtime.run_action_calls[2].command
    assert f'cd {expected_repo_path}' in set_url_cmd
    assert 'git remote set-url origin' in set_url_cmd
    assert 'git checkout -b' not in checkout_cmd  # Should not create a new branch
    assert result == 'repo'