def test_check_review_thread_with_git_patch():
    """Test that git patch from complete_runtime is included in the prompt."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GithubPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    review_thread = ReviewThread(
        comment='Please fix the formatting\n---\nlatest feedback:\nAdd docstrings',
        files=['/src/file1.py', '/src/file2.py'],
    )
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have fixed the formatting and added docstrings'
    git_patch = 'diff --git a/src/file1.py b/src/file1.py\n+"""Added docstring."""\n'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_review_thread(
            review_thread, issues_context, last_message, git_patch
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'Feedback:\n' + review_thread.comment in prompt
        assert (
            'Files locations:\n' + json.dumps(review_thread.files, indent=4) in prompt
        )
        assert 'Last message from AI agent:\n' + last_message in prompt
        assert 'Changes made (git patch):\n' + git_patch in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'