def test_guess_success_review_threads_litellm_call():
    """Test that the completion() call for review threads contains the expected content."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GithubPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create a mock issue with review threads
    issue = Issue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=None,
        closing_issues=['Issue 1 description', 'Issue 2 description'],
        review_comments=None,
        review_threads=[
            ReviewThread(
                comment='Please fix the formatting\n---\nlatest feedback:\nAdd docstrings',
                files=['/src/file1.py', '/src/file2.py'],
            ),
            ReviewThread(
                comment='Add more tests\n---\nlatest feedback:\nAdd test cases',
                files=['/tests/test_file.py'],
            ),
        ],
        thread_ids=['1', '2'],
        head_branch='test-branch',
    )

    # Create mock history with a detailed response
    history = [
        MessageAction(
            content="""I have made the following changes:
1. Fixed formatting in file1.py and file2.py
2. Added docstrings to all functions
3. Added test cases in test_file.py"""
        )
    ]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the feedback."""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the completion() calls
        assert mock_completion.call_count == 2  # One call per review thread

        # Check first call
        first_call = mock_completion.call_args_list[0]
        first_prompt = first_call[1]['messages'][0]['content']
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in first_prompt
        )
        assert (
            'Feedback:\nPlease fix the formatting\n---\nlatest feedback:\nAdd docstrings'
            in first_prompt
        )
        assert (
            'Files locations:\n'
            + json.dumps(['/src/file1.py', '/src/file2.py'], indent=4)
            in first_prompt
        )
        assert 'Last message from AI agent:\n' + history[0].content in first_prompt

        # Check second call
        second_call = mock_completion.call_args_list[1]
        second_prompt = second_call[1]['messages'][0]['content']
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in second_prompt
        )
        assert (
            'Feedback:\nAdd more tests\n---\nlatest feedback:\nAdd test cases'
            in second_prompt
        )
        assert (
            'Files locations:\n' + json.dumps(['/tests/test_file.py'], indent=4)
            in second_prompt
        )
        assert 'Last message from AI agent:\n' + history[0].content in second_prompt

        assert len(json.loads(explanation)) == 2