def test_initialize_repository_for_runtime_with_bitbucket_token(
    mock_event_stream, mock_get_file_store, mock_call_async_from_sync
):
    """Test that initialize_repository_for_runtime properly handles BITBUCKET_TOKEN."""
    from openhands.core.setup import initialize_repository_for_runtime
    from openhands.integrations.provider import ProviderType

    # Mock runtime
    mock_runtime = MagicMock()
    mock_runtime.clone_or_init_repo = AsyncMock(return_value='test-repo')
    mock_runtime.maybe_run_setup_script = MagicMock()
    mock_runtime.maybe_setup_git_hooks = MagicMock()

    # Mock call_async_from_sync to return the expected result
    mock_call_async_from_sync.return_value = 'test-repo'

    # Set up environment with BITBUCKET_TOKEN
    with patch.dict(os.environ, {'BITBUCKET_TOKEN': 'username:app_password'}):
        result = initialize_repository_for_runtime(
            runtime=mock_runtime, selected_repository='openhands/test-repo'
        )

    # Verify the result
    assert result == 'test-repo'

    # Verify that call_async_from_sync was called with the correct arguments
    mock_call_async_from_sync.assert_called_once()
    args, kwargs = mock_call_async_from_sync.call_args

    # Check that the function called was clone_or_init_repo
    assert args[0] == mock_runtime.clone_or_init_repo

    # Check that provider tokens were passed correctly
    provider_tokens = args[2]  # Third argument is immutable_provider_tokens
    assert provider_tokens is not None
    assert ProviderType.BITBUCKET in provider_tokens
    assert (
        provider_tokens[ProviderType.BITBUCKET].token.get_secret_value()
        == 'username:app_password'
    )

    # Check that the repository was passed correctly
    assert args[3] == 'openhands/test-repo'  # selected_repository
    assert args[4] is None