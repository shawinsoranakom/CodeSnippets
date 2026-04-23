def test_shape_execution_status_result_maps_all_fields():
    """shape_execution_status_result maps adapter fields to API response."""
    from langflow.api.v1.mappers.deployments.watsonx_orchestrate.mapper import WatsonxOrchestrateDeploymentMapper

    mapper = WatsonxOrchestrateDeploymentMapper()
    deployment_id = UUID("00000000-0000-0000-0000-000000000002")

    adapter_result = ExecutionStatusResult(
        execution_id="e-2",
        deployment_id="agent-2",
        provider_result={
            "execution_id": "e-2",
            "agent_id": "agent-2",
            "status": "completed",
            "result": {"output": "done"},
            "completed_at": "2026-01-01T00:01:00Z",
        },
    )

    response = mapper.shape_execution_status_result(adapter_result, deployment_id=deployment_id)
    assert response.deployment_id == deployment_id
    assert response.provider_data["id"] == "e-2"
    assert response.provider_data["status"] == "completed"
    assert response.provider_data["result"] == {"output": "done"}
    assert response.provider_data["completed_at"] == "2026-01-01T00:01:00Z"
    assert "deployment_id" not in response.provider_data
    assert "execution_id" not in response.provider_data