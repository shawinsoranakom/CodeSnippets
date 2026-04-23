def test_download_pr_from_gitlab():
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(GitlabPRHandler('owner', 'repo', 'token'), llm_config)
    mock_pr_response = MagicMock()
    mock_pr_response.json.side_effect = [
        [
            {
                'iid': 1,
                'title': 'PR 1',
                'description': 'This is a pull request',
                'source_branch': 'b1',
            },
            {
                'iid': 2,
                'title': 'My PR',
                'description': 'This is another pull request',
                'source_branch': 'b2',
            },
            {
                'iid': 3,
                'title': 'PR 3',
                'description': 'Final PR',
                'source_branch': 'b3',
            },
        ],
        None,
    ]
    mock_pr_response.raise_for_status = MagicMock()

    # Mock for related issues response
    mock_related_issuse_response = MagicMock()
    mock_related_issuse_response.json.return_value = [
        {'description': 'Issue 1 body', 'iid': 1},
        {'description': 'Issue 2 body', 'iid': 2},
    ]
    mock_related_issuse_response.raise_for_status = MagicMock()

    # Mock for PR comments response
    mock_comments_response = MagicMock()
    mock_comments_response.json.return_value = []  # No PR comments
    mock_comments_response.raise_for_status = MagicMock()

    # Mock for GraphQL request (for download_pr_metadata)
    mock_graphql_response = MagicMock()
    mock_graphql_response.json.side_effect = lambda: {
        'data': {
            'project': {
                'mergeRequest': {
                    'discussions': {
                        'edges': [
                            {
                                'node': {
                                    'id': '1',
                                    'resolved': False,
                                    'resolvable': True,
                                    'notes': {
                                        'nodes': [
                                            {
                                                'body': 'Unresolved comment 1',
                                                'position': {
                                                    'filePath': '/frontend/header.tsx',
                                                },
                                            },
                                            {
                                                'body': 'Follow up thread',
                                            },
                                        ]
                                    },
                                }
                            },
                            {
                                'node': {
                                    'id': '2',
                                    'resolved': True,
                                    'resolvable': True,
                                    'notes': {
                                        'nodes': [
                                            {
                                                'body': 'Resolved comment 1',
                                                'position': {
                                                    'filePath': '/some/file.py',
                                                },
                                            },
                                        ]
                                    },
                                }
                            },
                            {
                                'node': {
                                    'id': '3',
                                    'resolved': False,
                                    'resolvable': True,
                                    'notes': {
                                        'nodes': [
                                            {
                                                'body': 'Unresolved comment 3',
                                                'position': {
                                                    'filePath': '/another/file.py',
                                                },
                                            },
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
        if '/notes' in url:
            return mock_comments_response
        if '/related_issues' in url:
            return mock_related_issuse_response
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