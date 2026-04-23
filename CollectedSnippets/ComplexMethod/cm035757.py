async def test_clone_or_init_repo_gitlab_with_token(temp_dir, monkeypatch):
    config = OpenHandsConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    gitlab_token = 'gitlab_test_token'
    git_provider_tokens = MappingProxyType(
        {ProviderType.GITLAB: ProviderToken(token=SecretStr(gitlab_token))}
    )

    runtime = MockRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens,
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITLAB)

    result = await runtime.clone_or_init_repo(git_provider_tokens, 'owner/repo', None)

    # Verify that git clone, checkout, and git remote URL update were called
    assert len(runtime.run_action_calls) == 3  # clone, checkout, set-url
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)
    assert isinstance(runtime.run_action_calls[1], CmdRunAction)
    assert isinstance(runtime.run_action_calls[2], CmdRunAction)

    # Check that the first command is the git clone with the correct URL format with token
    clone_cmd = runtime.run_action_calls[0].command
    expected_repo_path = str(runtime.workspace_root / 'repo')
    assert f'https://oauth2:{gitlab_token}@gitlab.com/owner/repo.git' in clone_cmd
    assert expected_repo_path in clone_cmd

    # Check that the second command is the checkout
    checkout_cmd = runtime.run_action_calls[1].command
    assert f'cd {expected_repo_path}' in checkout_cmd
    assert 'git checkout -b openhands-workspace-' in checkout_cmd

    # Check that the third command sets the remote URL immediately after clone
    set_url_cmd = runtime.run_action_calls[2].command
    assert f'cd {expected_repo_path}' in set_url_cmd
    assert 'git remote set-url origin' in set_url_cmd
    assert gitlab_token in set_url_cmd

    assert result == 'repo'