async def test_list_versions_no_deployment_ids_returns_all(client: AsyncClient, logged_in_headers, monkeypatch):
    """Without deployment_ids filter, all versions are returned."""
    from uuid import UUID

    from langflow.services.deps import session_scope

    _set_deployments_feature_flag(monkeypatch, enabled=True)
    flow = await _create_flow(client, logged_in_headers)
    await _create_snapshot(client, logged_in_headers, flow["id"], description="deployed")
    await _create_snapshot(client, logged_in_headers, flow["id"], description="draft")

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
            name="test-no-filter",
            resource_key="rk-no-filter",
        )
        entries = await _list_versions(client, logged_in_headers, flow["id"])
        snap_deployed = next(e for e in entries if e["description"] == "deployed")
        await _attach_version_to_deployment(
            session,
            user_id=user_id,
            flow_version_id=UUID(snap_deployed["id"]),
            deployment_id=deployment.id,
        )

    # No filter — should return both versions
    entries = await _list_versions(client, logged_in_headers, flow["id"])
    assert len(entries) == 2
    deployed = next(e for e in entries if e["description"] == "deployed")
    draft = next(e for e in entries if e["description"] == "draft")
    assert deployed["is_deployed"] is True
    assert draft["is_deployed"] is False