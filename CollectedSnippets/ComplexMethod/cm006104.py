async def test_returns_paginated_flow_versions(
        self,
        mock_resolve,
        mock_list_flow_versions_synced,
    ):
        from langflow.api.v1.deployments import list_deployment_flow_versions

        deployment_row = _fake_deployment_row()
        adapter = AsyncMock()
        mapper = MagicMock()
        rows = [(SimpleNamespace(provider_snapshot_id="tool-1", created_at=None), SimpleNamespace())]
        snapshot_result = SnapshotListResult(
            snapshots=[
                SnapshotItem(
                    id="tool-1",
                    name="Tool 1",
                    provider_data={"connections": {"cfg-1": "conn-1"}},
                )
            ]
        )
        mock_resolve.return_value = (deployment_row, adapter, mapper, "watsonx-orchestrate")
        mock_list_flow_versions_synced.return_value = (rows, 7, snapshot_result)
        mapper.shape_flow_version_list_result.return_value = SimpleNamespace(
            page=2,
            size=5,
            total=7,
            flow_versions=[
                SimpleNamespace(
                    provider_snapshot_id="tool-1",
                    provider_data={"app_ids": ["cfg-1"]},
                )
            ],
        )

        flow_id = uuid4()
        response = await list_deployment_flow_versions(
            deployment_id=deployment_row.id,
            session=AsyncMock(),
            current_user=_fake_user(),
            page=2,
            size=5,
            flow_ids=[flow_id],
        )

        assert response.page == 2
        assert response.size == 5
        assert response.total == 7
        assert len(response.flow_versions) == 1
        assert response.flow_versions[0].provider_snapshot_id == "tool-1"
        assert response.flow_versions[0].provider_data == {"app_ids": ["cfg-1"]}

        mock_list_flow_versions_synced.assert_awaited_once()
        helper_kwargs = mock_list_flow_versions_synced.call_args.kwargs
        assert helper_kwargs["provider_id"] == deployment_row.deployment_provider_account_id
        assert helper_kwargs["deployment_id"] == deployment_row.id
        assert helper_kwargs["page"] == 2
        assert helper_kwargs["size"] == 5
        assert helper_kwargs["flow_ids"] == [flow_id]
        mapper.shape_flow_version_list_result.assert_called_once_with(
            rows=rows,
            snapshot_result=snapshot_result,
            page=2,
            size=5,
            total=7,
        )