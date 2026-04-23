def test_parse_webhook_comment_create(
        self, jira_dc_manager, sample_comment_webhook_payload
    ):
        """Test parsing comment creation webhook."""
        job_context = jira_dc_manager.parse_webhook(sample_comment_webhook_payload)

        assert job_context is not None
        assert job_context.issue_id == '12345'
        assert job_context.issue_key == 'PROJ-123'
        assert job_context.user_msg == 'Please fix this @openhands'
        assert job_context.user_email == 'user@company.com'
        assert job_context.display_name == 'Test User'
        assert job_context.workspace_name == 'jira.company.com'
        assert job_context.base_api_url == 'https://jira.company.com'