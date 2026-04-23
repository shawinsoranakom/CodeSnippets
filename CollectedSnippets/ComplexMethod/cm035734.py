async def test_search_branches_github_success_and_variables():
    service = GitHubService(token=SecretStr('t'))

    # Prepare a fake GraphQL response structure
    graphql_result = {
        'data': {
            'repository': {
                'refs': {
                    'nodes': [
                        {
                            'name': 'feature/bar',
                            'target': {
                                '__typename': 'Commit',
                                'oid': 'aaa111',
                                'committedDate': '2024-01-05T10:00:00Z',
                            },
                            'branchProtectionRule': {},  # indicates protected
                        },
                        {
                            'name': 'chore/update',
                            'target': {
                                '__typename': 'Tag',
                                'oid': 'should_be_ignored_for_commit',
                            },
                            'branchProtectionRule': None,
                        },
                    ]
                }
            }
        }
    }

    exec_mock = AsyncMock(return_value=graphql_result)
    with patch.object(service, 'execute_graphql_query', exec_mock) as mock_exec:
        branches = await service.search_branches('foo/bar', query='fe', per_page=999)

        # per_page should be clamped to <= 100 when passed to GraphQL variables
        args, kwargs = mock_exec.call_args
        _query = args[0]
        variables = args[1]
        assert variables['owner'] == 'foo'
        assert variables['name'] == 'bar'
        assert variables['query'] == 'fe'
        assert 1 <= variables['perPage'] <= 100

        assert len(branches) == 2
        b0, b1 = branches
        assert b0.name == 'feature/bar'
        assert b0.commit_sha == 'aaa111'
        assert b0.protected is True
        assert b0.last_push_date == '2024-01-05T10:00:00Z'

        # Non-commit target results in empty sha and no date
        assert b1.name == 'chore/update'
        assert b1.commit_sha == ''
        assert b1.last_push_date is None
        assert b1.protected is False