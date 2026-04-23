def test_pr_handler_get_converted_issues_with_specific_review_thread_comment():
    # Define the specific comment_id to filter
    specific_comment_id = 123

    # Mock GraphQL response for review threads
    with patch('httpx.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'iid': 1,
                'title': 'Test PR',
                'description': 'Test Body',
                'source_branch': 'test-branch',
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {
                'description': 'First comment',
                'id': 120,
                'resolvable': True,
                'system': False,
            },
            {
                'description': 'Second comment',
                'id': 124,
                'resolvable': True,
                'system': False,
            },
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'project': {
                    'mergeRequest': {
                        'discussions': {
                            'edges': [
                                {
                                    'node': {
                                        'id': 'review-thread-1',
                                        'resolved': False,
                                        'resolvable': True,
                                        'notes': {
                                            'nodes': [
                                                {
                                                    'id': f'GID/{specific_comment_id}',
                                                    'body': 'Specific review comment',
                                                    'position': {
                                                        'filePath': 'file1.txt',
                                                    },
                                                },
                                                {
                                                    'id': 'GID/456',
                                                    'body': 'Another review comment',
                                                    'position': {
                                                        'filePath': 'file1.txt',
                                                    },
                                                },
                                            ]
                                        },
                                    }
                                }
                            ]
                        },
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_empty_response,  # Third call for related issues
            mock_comments_response,  # Fourth call for PR comments
            mock_empty_response,  # Fifth call for PR comments (empty page)
        ]

        # Mock the post request for GraphQL
        with patch('httpx.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = ServiceContextPR(
                GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
            )

            # Get converted issues
            prs = handler.get_converted_issues(
                issue_numbers=[1], comment_id=specific_comment_id
            )

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments is None
            assert prs[0].review_comments is None
            assert len(prs[0].review_threads) == 1
            assert isinstance(prs[0].review_threads[0], ReviewThread)
            assert (
                prs[0].review_threads[0].comment
                == 'Specific review comment\n---\nlatest feedback:\nAnother review comment\n'
            )
            assert prs[0].review_threads[0].files == ['file1.txt']

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'