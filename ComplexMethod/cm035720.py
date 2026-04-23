def test_check_cmd_action_for_provider_token_ref():
    """Test detection of provider tokens in command actions"""
    # Test command with GitHub token
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')
    providers = ProviderHandler.check_cmd_action_for_provider_token_ref(cmd)
    assert ProviderType.GITHUB in providers
    assert len(providers) == 1

    # Test command with multiple tokens
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN && echo $GITLAB_TOKEN')
    providers = ProviderHandler.check_cmd_action_for_provider_token_ref(cmd)
    assert ProviderType.GITHUB in providers
    assert ProviderType.GITLAB in providers
    assert len(providers) == 2

    # Test command without tokens
    cmd = CmdRunAction(command='echo "Hello"')
    providers = ProviderHandler.check_cmd_action_for_provider_token_ref(cmd)
    assert len(providers) == 0

    # Test non-command action
    from openhands.events.action import MessageAction

    msg = MessageAction(content='test')
    providers = ProviderHandler.check_cmd_action_for_provider_token_ref(msg)
    assert len(providers) == 0