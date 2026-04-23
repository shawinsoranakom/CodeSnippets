def test_valid_agent_rejection_data(self):
        """Test creating valid AgentRejectionData."""
        data = AgentRejectionData(
            agent_name="Test Agent",
            graph_id="test-agent-123",
            graph_version=1,
            reviewer_name="Jane Doe",
            reviewer_email="jane@example.com",
            comments="Please fix the security issues before resubmitting.",
            reviewed_at=datetime.now(timezone.utc),
            resubmit_url="https://app.autogpt.com/build/test-agent-123",
        )

        assert data.agent_name == "Test Agent"
        assert data.graph_id == "test-agent-123"
        assert data.graph_version == 1
        assert data.reviewer_name == "Jane Doe"
        assert data.reviewer_email == "jane@example.com"
        assert data.comments == "Please fix the security issues before resubmitting."
        assert data.resubmit_url == "https://app.autogpt.com/build/test-agent-123"
        assert data.reviewed_at.tzinfo is not None