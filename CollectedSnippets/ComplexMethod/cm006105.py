async def test_get_deployment_does_not_inject_resource_key_into_provider_data(
        self,
        mock_resolve,
        mock_list_att,  # noqa: ARG002
    ):
        from langflow.api.v1.deployments import get_deployment
        from langflow.api.v1.mappers.deployments.base import BaseDeploymentMapper

        created_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 3, 4, 5, 6, tzinfo=timezone.utc)
        dep_row = _fake_deployment_row(
            resource_key="provider-rk-1",
            name="db-owned-name",
            description="db-owned-description",
            deployment_type="agent",
            created_at=created_at,
            updated_at=updated_at,
        )
        adapter = AsyncMock()
        provider_deployment = MagicMock()
        provider_deployment.name = "provider-owned-name"
        provider_deployment.description = "provider-owned-description"
        provider_deployment.type = "worker"
        provider_deployment.created_at = None
        provider_deployment.updated_at = None
        provider_deployment.model_dump.return_value = {
            "provider_data": {
                "llm": "virtual-model/bedrock/openai.gpt-oss-120b-1:0",
            }
        }
        adapter.get.return_value = provider_deployment
        mock_resolve.return_value = (dep_row, adapter, BaseDeploymentMapper(), "watsonx-orchestrate")

        session = AsyncMock()
        result = await get_deployment(deployment_id=dep_row.id, session=session, current_user=_fake_user())

        assert result.resource_key == "provider-rk-1"
        assert result.name == "db-owned-name"
        assert result.description == "db-owned-description"
        assert result.type == "agent"
        assert result.created_at == created_at
        assert result.updated_at == updated_at
        assert result.provider_data == {"llm": "virtual-model/bedrock/openai.gpt-oss-120b-1:0"}