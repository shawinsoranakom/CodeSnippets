def test_send_pull_request_with_reviewer(
    mock_get,
    mock_put,
    mock_post,
    mock_run,
    mock_issue,
    mock_output_dir,
    mock_llm_config,
):
    repo_path = os.path.join(mock_output_dir, 'repo')
    reviewer = 'test-reviewer'

    # Mock API responses
    mock_get.side_effect = [
        MagicMock(status_code=404),  # Branch doesn't exist
        MagicMock(json=lambda: {'default_branch': 'main'}),  # Get default branch
        MagicMock(json=lambda: [{'id': 123}]),  # Get user data
    ]

    # Mock PR creation response
    mock_post.side_effect = [
        MagicMock(
            status_code=200,
            json=lambda: {
                'web_url': 'https://gitlab.com/test-owner/test-repo/-/merge_requests/1',
                'iid': 1,
            },
        ),  # PR creation
    ]

    # Mock request reviewers response
    mock_put.side_effect = [
        MagicMock(status_code=200),  # Reviewer request
    ]

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Call the function with reviewer
    result = send_pull_request(
        issue=mock_issue,
        token='test-token',
        username='test-user',
        platform=ProviderType.GITLAB,
        patch_dir=repo_path,
        pr_type='ready',
        reviewer=reviewer,
    )

    # Assert API calls
    assert mock_get.call_count == 3
    assert mock_post.call_count == 1
    assert mock_put.call_count == 1

    # Check PR creation
    pr_create_call = mock_post.call_args_list[0]
    assert pr_create_call[1]['json']['title'] == 'Fix issue #42: Test Issue'

    # Check reviewer request
    reviewer_request_call = mock_put.call_args_list[0]
    assert (
        reviewer_request_call[0][0]
        == 'https://gitlab.com/api/v4/projects/test-owner%2Ftest-repo/merge_requests/1'
    )
    assert reviewer_request_call[1]['json'] == {'reviewer_ids': [123]}

    # Check the result URL
    assert result == 'https://gitlab.com/test-owner/test-repo/-/merge_requests/1'