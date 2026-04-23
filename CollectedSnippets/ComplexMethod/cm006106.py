def test_watsonx_mapper_is_registered() -> None:
    mapper = get_mapper(AdapterType.DEPLOYMENT, WATSONX_ORCHESTRATE_DEPLOYMENT_ADAPTER_KEY)
    assert isinstance(mapper, WatsonxOrchestrateDeploymentMapper)
    assert mapper.api_payloads.deployment_create is not None
    assert mapper.api_payloads.deployment_update is not None
    assert mapper.api_payloads.deployment_update_result is not None
    assert mapper.api_payloads.config_list_result is not None
    assert mapper.api_payloads.config_item_data is not None
    assert mapper.api_payloads.snapshot_list_result is not None