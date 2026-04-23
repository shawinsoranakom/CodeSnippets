def test_download_pr_with_review_comments():
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(GithubPRHandler('owner', 'repo', 'token'), llm_config)
    mock_pr_response = MagicMock()
    mock_pr_response.json.side_effect = [
        [
            {
                'number': 1,
                'title': 'PR 1',
                'body': 'This is a pull request',
                'head': {'ref': 'b1'},
            },
        ],
        None,
    ]
    mock_pr_response.raise_for_status = MagicMock()

    # Mock for PR comments response
    mock_comments_response = MagicMock()
    mock_comments_response.json.return_value = []  # No PR comments
    mock_comments_response.raise_for_status = MagicMock()

    # Mock for GraphQL request with review comments but no threads
    mock_graphql_response = MagicMock()
    mock_graphql_response.json.side_effect = lambda: {
        'data': {
            'repository': {
                'pullRequest': {
                    'closingIssuesReferences': {'edges': []},
                    'reviews': {
                        'nodes': [
                            {'body': 'Please fix this typo'},
                            {'body': 'Add more tests'},
                        ]
                    },
                }
            }
        }
    }

    mock_graphql_response.raise_for_status = MagicMock()

    def get_mock_response(url, *args, **kwargs):
        if '/comments' in url:
            return mock_comments_response
        return mock_pr_response

    with patch('httpx.get', side_effect=get_mock_response):
        with patch('httpx.post', return_value=mock_graphql_response):
            issues = handler.get_converted_issues(issue_numbers=[1])

    assert len(issues) == 1
    assert handler.issue_type == 'pr'
    assert isinstance(issues[0], Issue)
    assert issues[0].number == 1
    assert issues[0].title == 'PR 1'
    assert issues[0].head_branch == 'b1'

    # Verify review comments are set but threads are empty
    assert len(issues[0].review_comments) == 2
    assert issues[0].review_comments[0] == 'Please fix this typo'
    assert issues[0].review_comments[1] == 'Add more tests'
    assert not issues[0].review_threads
    assert not issues[0].closing_issues
    assert not issues[0].thread_ids