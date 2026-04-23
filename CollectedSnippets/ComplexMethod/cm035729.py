async def test_get_paginated_branches_gitlab_headers_and_parsing():
    service = GitLabService(token=SecretStr('t'))

    mock_response = [
        {
            'name': 'main',
            'commit': {'id': 'abc', 'committed_date': '2024-01-01T00:00:00Z'},
            'protected': True,
        },
        {
            'name': 'dev',
            'commit': {'id': 'def', 'committed_date': '2024-01-02T00:00:00Z'},
            'protected': False,
        },
    ]

    headers = {
        'X-Total': '42',
        'Link': '<https://gitlab.example.com/api/v4/projects/group%2Frepo/repository/branches?page=3&per_page=2>; rel="next"',  # indicates has next page
    }

    with patch.object(service, '_make_request', return_value=(mock_response, headers)):
        res = await service.get_paginated_branches('group/repo', page=2, per_page=2)

        assert isinstance(res, PaginatedBranchesResponse)
        assert res.has_next_page is True
        assert res.current_page == 2
        assert res.per_page == 2
        assert res.total_count == 42
        assert len(res.branches) == 2
        assert res.branches[0] == Branch(
            name='main',
            commit_sha='abc',
            protected=True,
            last_push_date='2024-01-01T00:00:00Z',
        )
        assert res.branches[1] == Branch(
            name='dev',
            commit_sha='def',
            protected=False,
            last_push_date='2024-01-02T00:00:00Z',
        )