def test_download_pr_from_github():
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
            {
                'number': 2,
                'title': 'My PR',
                'body': 'This is another pull request',
                'head': {'ref': 'b2'},
            },
            {'number': 3, 'title': 'PR 3', 'body': 'Final PR', 'head': {'ref': 'b3'}},
        ],
        None,
    ]
    mock_pr_response.raise_for_status = MagicMock()

    # Mock for PR comments response
    mock_comments_response = MagicMock()
    mock_comments_response.json.return_value = []  # No PR comments
    mock_comments_response.raise_for_status = MagicMock()

    # Mock for GraphQL request (for download_pr_metadata)
    mock_graphql_response = MagicMock()
    mock_graphql_response.json.side_effect = lambda: {
        'data': {
            'repository': {
                'pullRequest': {
                    'closingIssuesReferences': {
                        'edges': [
                            {'node': {'body': 'Issue 1 body', 'number': 1}},
                            {'node': {'body': 'Issue 2 body', 'number': 2}},
                        ]
                    },
                    'reviewThreads': {
                        'edges': [
                            {
                                'node': {
                                    'isResolved': False,
                                    'id': '1',
                                    'comments': {
                                        'nodes': [
                                            {
                                                'body': 'Unresolved comment 1',
                                                'path': '/frontend/header.tsx',
                                            },
                                            {'body': 'Follow up thread'},
                                        ]
                                    },
                                }
                            },
                            {
                                'node': {
                                    'isResolved': True,
                                    'id': '2',
                                    'comments': {
                                        'nodes': [
                                            {
                                                'body': 'Resolved comment 1',
                                                'path': '/some/file.py',
                                            }
                                        ]
                                    },
                                }
                            },
                            {
                                'node': {
                                    'isResolved': False,
                                    'id': '3',
                                    'comments': {
                                        'nodes': [
                                            {
                                                'body': 'Unresolved comment 3',
                                                'path': '/another/file.py',
                                            }
                                        ]
                                    },
                                }
                            },
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
            issues = handler.get_converted_issues(issue_numbers=[1, 2, 3])

    assert len(issues) == 3
    assert handler.issue_type == 'pr'
    assert all(isinstance(issue, Issue) for issue in issues)
    assert [issue.number for issue in issues] == [1, 2, 3]
    assert [issue.title for issue in issues] == ['PR 1', 'My PR', 'PR 3']
    assert [issue.head_branch for issue in issues] == ['b1', 'b2', 'b3']

    assert len(issues[0].review_threads) == 2  # Only unresolved threads
    assert (
        issues[0].review_threads[0].comment
        == 'Unresolved comment 1\n---\nlatest feedback:\nFollow up thread\n'
    )
    assert issues[0].review_threads[0].files == ['/frontend/header.tsx']
    assert (
        issues[0].review_threads[1].comment
        == 'latest feedback:\nUnresolved comment 3\n'
    )
    assert issues[0].review_threads[1].files == ['/another/file.py']
    assert issues[0].closing_issues == ['Issue 1 body', 'Issue 2 body']
    assert issues[0].thread_ids == ['1', '3']