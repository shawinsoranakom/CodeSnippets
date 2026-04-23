def test_create_job_response_structure(self):
        """Test job response structure and timestamp format."""
        job_id = uuid4()
        flow_id = "flow-678"
        response = create_job_response(str(job_id), flow_id)

        assert isinstance(response, WorkflowJobResponse)
        assert response.job_id == job_id
        assert response.flow_id == flow_id
        assert response.status == JobStatus.QUEUED
        assert response.errors == []
        assert response.created_timestamp is not None
        # Verify timestamp format (ISO format should contain 'T')
        assert isinstance(response.created_timestamp, str)
        assert "T" in response.created_timestamp