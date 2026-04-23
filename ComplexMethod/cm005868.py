def test_payload_schema_slot_registered_for_deployment_update() -> None:
    slot = WatsonxOrchestrateDeploymentService.payload_schemas
    assert slot is not None
    assert slot.deployment_create is not None
    assert slot.deployment_create.adapter_model is WatsonxDeploymentCreatePayload
    assert slot.flow_artifact is not None
    assert slot.flow_artifact.adapter_model is WatsonxFlowArtifactProviderData
    assert slot.deployment_create_result is not None
    assert slot.deployment_create_result.adapter_model is WatsonxDeploymentCreateResultData
    assert slot.deployment_update is not None
    assert slot.deployment_update.adapter_model is WatsonxDeploymentUpdatePayload
    assert slot.deployment_update_result is not None
    assert slot.deployment_update_result.adapter_model is WatsonxDeploymentUpdateResultData
    assert slot.execution_create_result is not None
    assert slot.execution_create_result.adapter_model is WatsonxAgentExecutionResultData
    assert slot.execution_status_result is not None
    assert slot.execution_status_result.adapter_model is WatsonxAgentExecutionResultData