async def test_gitlab_search_repositories_url_parsing():
    """Test that search_repositories correctly parses GitLab URLs when public=True."""
    service = GitLabService(token=SecretStr('test-token'))

    # Test URL parsing method directly
    assert service._parse_gitlab_url('https://gitlab.com/group/repo') == 'group/repo'
    assert (
        service._parse_gitlab_url('https://gitlab.com/group/subgroup/repo')
        == 'group/subgroup/repo'
    )
    assert (
        service._parse_gitlab_url('https://gitlab.example.com/org/team/project')
        == 'org/team/project'
    )
    assert service._parse_gitlab_url('https://gitlab.com/group/repo/') == 'group/repo'
    assert (
        service._parse_gitlab_url('https://gitlab.com/group/') is None
    )  # Missing repo
    assert service._parse_gitlab_url('https://gitlab.com/') is None  # Empty path
    assert service._parse_gitlab_url('invalid-url') is None