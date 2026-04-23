async def test_list_versions_is_deployed_true_when_attached(client: AsyncClient, logged_in_headers, monkeypatch):
    """Versions attached to a deployment should have is_deployed=True."""
    from uuid import UUID

    from langflow.services.deps import session_scope

    _set_deployments_feature_flag(monkeypatch, enabled=True)
    flow = await _create_flow(client, logged_in_headers)
    snap = await _create_snapshot(client, logged_in_headers, flow["id"])
    snap2 = await _create_snapshot(client, logged_in_headers, flow["id"], description="undeployed")

    async with session_scope() as session:
        from langflow.services.database.models.flow.model import Flow
        from sqlmodel import select

        flow_row = (await session.exec(select(Flow).where(Flow.id == UUID(flow["id"])))).one()
        user_id = flow_row.user_id
        project_id = flow_row.folder_id
        provider_account = await _create_provider_account_row(session, user_id=user_id)
        deployment = await _create_deployment_row(
            session,
            user_id=user_id,
            project_id=project_id,
            provider_account_id=provider_account.id,
            name="test-deployment",
            resource_key="rk-1",
        )
        await _attach_version_to_deployment(
            session,
            user_id=user_id,
            flow_version_id=UUID(snap["id"]),
            deployment_id=deployment.id,
        )

    entries = await _list_versions(client, logged_in_headers, flow["id"])
    assert len(entries) == 2
    deployed_entry = next(e for e in entries if e["id"] == snap["id"])
    undeployed_entry = next(e for e in entries if e["id"] == snap2["id"])
    assert deployed_entry["is_deployed"] is True
    assert undeployed_entry["is_deployed"] is False