async def test_list_versions_filter_by_deployment_ids(client: AsyncClient, logged_in_headers, monkeypatch):
    """Filtering by deployment_ids returns only versions attached to those deployments."""
    from uuid import UUID

    from langflow.services.deps import session_scope

    _set_deployments_feature_flag(monkeypatch, enabled=True)
    flow = await _create_flow(client, logged_in_headers)
    snap1 = await _create_snapshot(client, logged_in_headers, flow["id"], description="deployed-to-d1")
    snap2 = await _create_snapshot(client, logged_in_headers, flow["id"], description="deployed-to-d2")
    await _create_snapshot(client, logged_in_headers, flow["id"], description="not-deployed")

    async with session_scope() as session:
        from langflow.services.database.models.flow.model import Flow
        from sqlmodel import select

        flow_row = (await session.exec(select(Flow).where(Flow.id == UUID(flow["id"])))).one()
        user_id = flow_row.user_id
        project_id = flow_row.folder_id
        provider_account = await _create_provider_account_row(session, user_id=user_id)
        d1 = await _create_deployment_row(
            session,
            user_id=user_id,
            project_id=project_id,
            provider_account_id=provider_account.id,
            name="deploy-filter-1",
            resource_key="rk-filter-1",
        )
        d2 = await _create_deployment_row(
            session,
            user_id=user_id,
            project_id=project_id,
            provider_account_id=provider_account.id,
            name="deploy-filter-2",
            resource_key="rk-filter-2",
        )
        await _attach_version_to_deployment(
            session,
            user_id=user_id,
            flow_version_id=UUID(snap1["id"]),
            deployment_id=d1.id,
        )
        await _attach_version_to_deployment(
            session,
            user_id=user_id,
            flow_version_id=UUID(snap2["id"]),
            deployment_id=d2.id,
        )
        d1_id = str(d1.id)
        d2_id = str(d2.id)

    # Filter by d1 only
    resp = await client.get(
        f"api/v1/flows/{flow['id']}/versions/",
        params={"deployment_ids": d1_id},
        headers=logged_in_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    entries = resp.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["id"] == snap1["id"]
    assert entries[0]["is_deployed"] is True

    # Filter by both d1 and d2
    resp = await client.get(
        f"api/v1/flows/{flow['id']}/versions/",
        params=[("deployment_ids", d1_id), ("deployment_ids", d2_id)],
        headers=logged_in_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    entries = resp.json()["entries"]
    assert len(entries) == 2
    entry_ids = {e["id"] for e in entries}
    assert snap1["id"] in entry_ids
    assert snap2["id"] in entry_ids