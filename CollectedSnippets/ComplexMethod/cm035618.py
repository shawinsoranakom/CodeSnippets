def test_send_pull_request(
    mock_get,
    mock_post,
    mock_run,
    mock_issue,
    mock_llm_config,
    mock_output_dir,
    pr_type,
    target_branch,
    pr_title,
):
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API responses based on whether target_branch is specified
    if target_branch:
        mock_get.side_effect = [
            MagicMock(status_code=404),  # Branch doesn't exist
            MagicMock(status_code=200),  # Target branch exists
        ]
    else:
        mock_get.side_effect = [
            MagicMock(status_code=404),  # Branch doesn't exist
            MagicMock(json=lambda: {'default_branch': 'main'}),  # Get default branch
        ]

    mock_post.return_value.json.return_value = {
        'html_url': 'https://github.com/test-owner/test-repo/pull/1'
    }

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Call the function
    result = send_pull_request(
        issue=mock_issue,
        token='test-token',
        username='test-user',
        platform=ProviderType.GITHUB,
        patch_dir=repo_path,
        pr_type=pr_type,
        target_branch=target_branch,
        pr_title=pr_title,
    )

    # Assert API calls
    expected_get_calls = 2
    assert mock_get.call_count == expected_get_calls

    # Check branch creation and push
    assert mock_run.call_count == 2
    checkout_call, push_call = mock_run.call_args_list

    assert checkout_call == call(
        ['git', '-C', repo_path, 'checkout', '-b', 'openhands-fix-issue-42'],
        capture_output=True,
        text=True,
    )
    assert push_call == call(
        [
            'git',
            '-C',
            repo_path,
            'push',
            'https://test-user:test-token@github.com/test-owner/test-repo.git',
            'openhands-fix-issue-42',
        ],
        capture_output=True,
        text=True,
    )

    # Check PR creation based on pr_type
    if pr_type == 'branch':
        assert (
            result
            == 'https://github.com/test-owner/test-repo/compare/openhands-fix-issue-42?expand=1'
        )
        mock_post.assert_not_called()
    else:
        assert result == 'https://github.com/test-owner/test-repo/pull/1'
        mock_post.assert_called_once()
        post_data = mock_post.call_args[1]['json']
        expected_title = pr_title if pr_title else 'Fix issue #42: Test Issue'
        assert post_data['title'] == expected_title
        assert post_data['body'].startswith('This pull request fixes #42.')
        assert post_data['head'] == 'openhands-fix-issue-42'
        assert post_data['base'] == (target_branch if target_branch else 'main')
        assert post_data['draft'] == (pr_type == 'draft')