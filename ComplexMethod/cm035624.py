async def test_process_issue(
    default_mock_args,
    mock_github_token,
    mock_output_dir,
    mock_user_instructions_template,
    test_case,
):
    """Test the process_issue method with different scenarios."""
    # Set up test data
    issue = Issue(
        owner='test_owner',
        repo='test_repo',
        number=1,
        title='Test Issue',
        body='This is a test issue',
    )
    base_commit = 'abcdef1234567890'

    # Customize the mock args for this test
    default_mock_args.output_dir = mock_output_dir
    default_mock_args.issue_type = 'pr' if test_case.get('is_pr', False) else 'issue'

    # Create a resolver instance with mocked token identification
    resolver = IssueResolver(default_mock_args)
    resolver.user_instructions_prompt_template = mock_user_instructions_template

    # Mock the handler with LLM config
    llm_config = LLMConfig(model='test', api_key='test')
    handler_instance = MagicMock()
    handler_instance.guess_success.return_value = (
        test_case['expected_success'],
        test_case.get('comment_success', None),
        test_case['expected_explanation'],
    )
    handler_instance.get_instruction.return_value = (
        'Test instruction',
        'Test conversation instructions',
        [],
    )
    handler_instance.issue_type = 'pr' if test_case.get('is_pr', False) else 'issue'
    handler_instance.llm = LLM(llm_config, service_id='test-service')

    # Mock the runtime and its methods
    mock_runtime = MagicMock()
    mock_runtime.connect = AsyncMock()
    mock_runtime.run_action.return_value = CmdOutputObservation(
        content='test patch',
        command='git diff',
        metadata=CmdOutputMetadata(exit_code=0),
    )
    mock_runtime.event_stream.subscribe = MagicMock()

    # Mock the create_runtime function
    mock_create_runtime = MagicMock(return_value=mock_runtime)

    # Mock the run_controller function
    mock_run_controller = AsyncMock()
    if test_case['run_controller_raises']:
        mock_run_controller.side_effect = test_case['run_controller_raises']
    else:
        mock_run_controller.return_value = test_case['run_controller_return']

    # Patch the necessary functions and methods
    with (
        patch('openhands.resolver.issue_resolver.create_runtime', mock_create_runtime),
        patch('openhands.resolver.issue_resolver.run_controller', mock_run_controller),
        patch.object(
            resolver, 'complete_runtime', return_value={'git_patch': 'test patch'}
        ),
        patch.object(resolver, 'initialize_runtime') as mock_initialize_runtime,
    ):
        # Call the process_issue method
        result = await resolver.process_issue(issue, base_commit, handler_instance)

        # Assert the result matches our expectations
        assert isinstance(result, ResolverOutput)
        assert result.issue == issue
        assert result.base_commit == base_commit
        assert result.git_patch == 'test patch'
        assert result.success == test_case['expected_success']
        assert result.result_explanation == test_case['expected_explanation']
        assert result.error == test_case['expected_error']

        # Assert that the mocked functions were called
        mock_create_runtime.assert_called_once()
        mock_runtime.connect.assert_called_once()
        mock_initialize_runtime.assert_called_once()
        mock_run_controller.assert_called_once()
        resolver.complete_runtime.assert_awaited_once_with(mock_runtime, base_commit)

        # Assert run_controller was called with the right parameters
        if not test_case['run_controller_raises']:
            # Check that the first positional argument is a config
            assert 'config' in mock_run_controller.call_args[1]
            # Check that initial_user_action is a MessageAction with the right content
            assert isinstance(
                mock_run_controller.call_args[1]['initial_user_action'], MessageAction
            )
            assert mock_run_controller.call_args[1]['runtime'] == mock_runtime

        # Assert that guess_success was called only for successful runs
        if test_case['expected_success']:
            handler_instance.guess_success.assert_called_once()
        else:
            handler_instance.guess_success.assert_not_called()