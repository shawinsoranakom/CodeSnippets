def test_initialize_repository_for_runtime_with_multiple_tokens(
    mock_event_stream, mock_get_file_store, mock_call_async_from_sync
):
    """Test that initialize_repository_for_runtime handles multiple provider tokens including Bitbucket."""
    from openhands.core.setup import initialize_repository_for_runtime
    from openhands.integrations.provider import ProviderType

    # Mock runtime
    mock_runtime = MagicMock()
    mock_runtime.clone_or_init_repo = AsyncMock(return_value='test-repo')
    mock_runtime.maybe_run_setup_script = MagicMock()
    mock_runtime.maybe_setup_git_hooks = MagicMock()

    # Mock call_async_from_sync to return the expected result
    mock_call_async_from_sync.return_value = 'test-repo'

    # Set up environment with multiple tokens
    with patch.dict(
        os.environ,
        {
            'GITHUB_TOKEN': 'github_token_123',
            'GITLAB_TOKEN': 'gitlab_token_456',
            'BITBUCKET_TOKEN': 'username:bitbucket_app_password',
        },
    ):
        result = initialize_repository_for_runtime(
            runtime=mock_runtime, selected_repository='openhands/test-repo'
        )

    # Verify the result
    assert result == 'test-repo'

    # Verify that call_async_from_sync was called
    mock_call_async_from_sync.assert_called_once()
    args, kwargs = mock_call_async_from_sync.call_args

    # Check that provider tokens were passed correctly
    provider_tokens = args[2]  # Third argument is immutable_provider_tokens
    assert provider_tokens is not None

    # Verify all three provider types are present
    assert ProviderType.GITHUB in provider_tokens
    assert ProviderType.GITLAB in provider_tokens
    assert ProviderType.BITBUCKET in provider_tokens

    # Verify token values
    assert (
        provider_tokens[ProviderType.GITHUB].token.get_secret_value()
        == 'github_token_123'
    )
    assert (
        provider_tokens[ProviderType.GITLAB].token.get_secret_value()
        == 'gitlab_token_456'
    )
    assert (
        provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()
        == 'username:bitbucket_app_password'
    )