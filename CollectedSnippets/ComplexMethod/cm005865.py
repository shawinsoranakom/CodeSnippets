def test_shape_execution_create_result_maps_all_fields():
    """shape_execution_create_result maps adapter fields to API response."""
    from langflow.api.v1.mappers.deployments.watsonx_orchestrate.mapper import WatsonxOrchestrateDeploymentMapper

    mapper = WatsonxOrchestrateDeploymentMapper()
    deployment_id = UUID("00000000-0000-0000-0000-000000000001")

    adapter_result = ExecutionCreateResult(
        execution_id="e-1",
        deployment_id="agent-1",
        provider_result={
            "execution_id": "e-1",
            "agent_id": "agent-1",
            "status": "accepted",
            "started_at": "2026-01-01T00:00:00Z",
        },
    )

    response = mapper.shape_execution_create_result(adapter_result, deployment_id=deployment_id)
    assert response.deployment_id == deployment_id
    assert response.provider_data["id"] == "e-1"
    assert response.provider_data["status"] == "accepted"
    assert response.provider_data["started_at"] == "2026-01-01T00:00:00Z"
    assert response.provider_data["agent_id"] == "agent-1"
    assert "deployment_id" not in response.provider_data
    assert "execution_id" not in response.provider_data