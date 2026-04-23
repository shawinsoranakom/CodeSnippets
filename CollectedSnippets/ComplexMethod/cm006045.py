async def test_syncs_snapshots_with_snapshot_ids_and_returns_enrichment(
        self,
        mock_list_attachments,
        mock_sync_snapshot_ids,
        mock_list_with_versions,
        mock_count_attachments,
    ):
        deployment_id = uuid4()
        attachments = [
            _mock_attachment(provider_snapshot_id="snap-1", deployment_id=deployment_id),
            _mock_attachment(provider_snapshot_id="snap-stale", deployment_id=deployment_id),
            _mock_attachment(provider_snapshot_id=None, deployment_id=deployment_id),
        ]
        mock_list_attachments.return_value = attachments
        rows = [(SimpleNamespace(provider_snapshot_id="snap-1"), SimpleNamespace())]
        mock_list_with_versions.return_value = rows

        adapter = AsyncMock()
        adapter.list_snapshots.return_value = SnapshotListResult(
            snapshots=[
                SnapshotItem(
                    id="snap-1",
                    name="tool-1",
                    provider_data={"connections": {"cfg-1": "conn-1"}},
                )
            ]
        )
        mapper = WatsonxOrchestrateDeploymentMapper()
        db = MagicMock()
        db.begin_nested.return_value = _AsyncNoopSavepoint()

        from langflow.api.v1.mappers.deployments.helpers import list_deployment_flow_versions_synced

        out_rows, total, snapshot_result = await list_deployment_flow_versions_synced(
            deployment_adapter=adapter,
            deployment_mapper=mapper,
            user_id=uuid4(),
            provider_id=uuid4(),
            deployment_id=deployment_id,
            db=db,
            page=2,
            size=3,
        )

        assert out_rows == rows
        assert total == 2
        assert isinstance(snapshot_result, SnapshotListResult)
        assert [snapshot.id for snapshot in snapshot_result.snapshots] == ["snap-1"]
        adapter.list_snapshots.assert_awaited_once()
        adapter_params = adapter.list_snapshots.call_args.kwargs["params"]
        assert adapter_params.snapshot_ids == ["snap-1", "snap-stale"]
        mock_sync_snapshot_ids.assert_awaited_once()
        assert mock_sync_snapshot_ids.call_args.kwargs["known_snapshot_ids"] == {"snap-1"}
        assert mock_list_with_versions.call_args.kwargs["offset"] == 3
        assert mock_list_with_versions.call_args.kwargs["limit"] == 3
        mock_count_attachments.assert_awaited_once()