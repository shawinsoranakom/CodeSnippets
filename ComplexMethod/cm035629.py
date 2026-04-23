def test_pr_handler_get_converted_issues_with_comments():
    # Mock the necessary dependencies
    with patch('httpx.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR',
                'body': 'Test Body fixes #1',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment'},
            {'body': 'Second comment'},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {'edges': []},
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        # Mock the response for fetching the external issue referenced in PR body
        mock_external_issue_response = MagicMock()
        mock_external_issue_response.json.return_value = {
            'body': 'This is additional context from an externally referenced issue.'
        }

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
            mock_external_issue_response,  # Mock response for the external issue reference #1
        ]

        # Mock the post request for GraphQL
        with patch('httpx.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = ServiceContextPR(
                GithubPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
            )

            # Get converted issues
            prs = handler.get_converted_issues(issue_numbers=[1])

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments == ['First comment', 'Second comment']

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body fixes #1'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'
            assert prs[0].closing_issues == [
                'This is additional context from an externally referenced issue.'
            ]