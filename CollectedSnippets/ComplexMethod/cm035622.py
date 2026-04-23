def test_download_issues_from_github():
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextIssue(
        GithubIssueHandler('owner', 'repo', 'token'), llm_config
    )

    mock_issues_response = MagicMock()
    mock_issues_response.json.side_effect = [
        [
            {'number': 1, 'title': 'Issue 1', 'body': 'This is an issue'},
            {
                'number': 2,
                'title': 'PR 1',
                'body': 'This is a pull request',
                'pull_request': {},
            },
            {'number': 3, 'title': 'Issue 2', 'body': 'This is another issue'},
        ],
        None,
    ]
    mock_issues_response.raise_for_status = MagicMock()

    mock_comments_response = MagicMock()
    mock_comments_response.json.return_value = []
    mock_comments_response.raise_for_status = MagicMock()

    def get_mock_response(url, *args, **kwargs):
        if '/comments' in url:
            return mock_comments_response
        return mock_issues_response

    with patch('httpx.get', side_effect=get_mock_response):
        issues = handler.get_converted_issues(issue_numbers=[1, 3])

    assert len(issues) == 2
    assert handler.issue_type == 'issue'
    assert all(isinstance(issue, Issue) for issue in issues)
    assert [issue.number for issue in issues] == [1, 3]
    assert [issue.title for issue in issues] == ['Issue 1', 'Issue 2']
    assert [issue.review_comments for issue in issues] == [None, None]
    assert [issue.closing_issues for issue in issues] == [None, None]
    assert [issue.thread_ids for issue in issues] == [None, None]