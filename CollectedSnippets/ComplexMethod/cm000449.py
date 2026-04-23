def test_model_serialization(self):
        """Test that models can be serialized and deserialized."""
        original_data = AgentRejectionData(
            agent_name="Test Agent",
            graph_id="test-agent-123",
            graph_version=1,
            reviewer_name="Jane Doe",
            reviewer_email="jane@example.com",
            comments="Please fix the issues.",
            reviewed_at=datetime.now(timezone.utc),
            resubmit_url="https://app.autogpt.com/build/test-agent-123",
        )

        # Serialize to dict
        data_dict = original_data.model_dump()

        # Deserialize back
        restored_data = AgentRejectionData.model_validate(data_dict)

        assert restored_data.agent_name == original_data.agent_name
        assert restored_data.graph_id == original_data.graph_id
        assert restored_data.graph_version == original_data.graph_version
        assert restored_data.reviewer_name == original_data.reviewer_name
        assert restored_data.reviewer_email == original_data.reviewer_email
        assert restored_data.comments == original_data.comments
        assert restored_data.reviewed_at == original_data.reviewed_at
        assert restored_data.resubmit_url == original_data.resubmit_url