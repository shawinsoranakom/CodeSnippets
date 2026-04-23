def test_valid_agent_approval_data(self):
        """Test creating valid AgentApprovalData."""
        data = AgentApprovalData(
            agent_name="Test Agent",
            graph_id="test-agent-123",
            graph_version=1,
            reviewer_name="John Doe",
            reviewer_email="john@example.com",
            comments="Great agent, approved!",
            reviewed_at=datetime.now(timezone.utc),
            store_url="https://app.autogpt.com/store/test-agent-123",
        )

        assert data.agent_name == "Test Agent"
        assert data.graph_id == "test-agent-123"
        assert data.graph_version == 1
        assert data.reviewer_name == "John Doe"
        assert data.reviewer_email == "john@example.com"
        assert data.comments == "Great agent, approved!"
        assert data.store_url == "https://app.autogpt.com/store/test-agent-123"
        assert data.reviewed_at.tzinfo is not None