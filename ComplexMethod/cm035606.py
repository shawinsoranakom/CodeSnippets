def test_get_converted_issues_handles_empty_body():
    # Mock the necessary dependencies
    with patch('httpx.get') as mock_get:
        # Mock the response for issues
        mock_issues_response = MagicMock()
        mock_issues_response.json.return_value = [
            {'iid': 1, 'title': 'Test Issue', 'description': None}
        ]
        # Mock the response for comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = []
        # Set up the mock to return different responses
        mock_get.side_effect = [
            mock_issues_response,
            mock_comments_response,
            mock_comments_response,
        ]

        # Create an instance of IssueHandler
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextIssue(
            GitlabIssueHandler('test-owner', 'test-repo', 'test-token'), llm_config
        )

        # Get converted issues
        issues = handler.get_converted_issues(issue_numbers=[1])

        # Verify that we got exactly one issue
        assert len(issues) == 1

        # Verify that body is empty string when None
        assert issues[0].body == ''

        # Verify other fields are set correctly
        assert issues[0].number == 1
        assert issues[0].title == 'Test Issue'
        assert issues[0].owner == 'test-owner'
        assert issues[0].repo == 'test-repo'

        # Verify that review_comments is initialized as None
        assert issues[0].review_comments is None