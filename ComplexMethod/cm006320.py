async def list_snapshots(
        self,
        *,
        user_id: IdLike,
        params: SnapshotListParams | None = None,
        db: AsyncSession,
    ) -> SnapshotListResult:
        """List snapshots visible to this adapter.

        Supports four modes:
        - **deployment-scoped**: requires exactly one ``deployment_id`` in params;
          returns tools bound to that agent.
        - **snapshot-ids-only**: when ``snapshot_ids`` is provided and
          ``deployment_ids`` is empty/None, fetches tools directly by ID to
          verify which ones still exist in the provider.
        - **snapshot-names**: when ``snapshot_names`` is provided and
          ``deployment_ids`` is empty/None, fetches tools by name to check
          which ones exist in the provider tenant.
        - **tenant-scoped**: when neither deployment_ids nor snapshot_ids are
          provided, returns all draft tools visible in the provider tenant.
        """
        has_deployment_ids = params and params.deployment_ids
        has_snapshot_ids = params and params.snapshot_ids
        has_snapshot_names = params and params.snapshot_names

        if has_snapshot_ids and has_deployment_ids:
            logger.warning(
                "list_snapshots called with both deployment_ids and snapshot_ids; "
                "snapshot_ids will be ignored in favour of the deployment-scoped path"
            )

        clients = await self._get_provider_clients(user_id=user_id, db=db)

        if has_snapshot_ids and not has_deployment_ids:
            return await verify_tools_by_ids(clients, params.snapshot_ids)  # type: ignore[union-attr]
        if has_snapshot_names and not has_deployment_ids:
            try:
                raw_tools = await asyncio.to_thread(clients.tool.get_drafts_by_names, params.snapshot_names)  # type: ignore[union-attr]
            except Exception as exc:  # noqa: BLE001
                raise_as_deployment_error(
                    exc,
                    error_prefix=ErrorPrefix.LIST,
                    log_msg="Unexpected error while listing wxO snapshots by name",
                )
            snapshots = [
                SnapshotItem(
                    id=tool["id"],
                    name=tool.get("name") or tool["id"],
                    provider_data=self._validate_snapshot_item_provider_data(
                        {"connections": extract_langflow_connections_binding(tool)}
                    ),
                )
                for tool in (raw_tools or [])
                if isinstance(tool, dict) and tool.get("id")
            ]
            return SnapshotListResult(
                snapshots=snapshots,
                provider_result=self.payload_schemas.snapshot_list_result.parse({}).model_dump(exclude_none=True),
            )
        if not has_deployment_ids:
            try:
                raw_tools = await asyncio.to_thread(clients.get_tools_raw)
            except Exception as exc:  # noqa: BLE001
                raise_as_deployment_error(
                    exc,
                    error_prefix=ErrorPrefix.LIST,
                    log_msg="Unexpected error while listing wxO tenant snapshots",
                )
            snapshots = [
                SnapshotItem(
                    id=tool["id"],
                    name=tool.get("name") or tool["id"],
                    provider_data=self._validate_snapshot_item_provider_data(
                        {"connections": extract_langflow_connections_binding(tool)}
                    ),
                )
                for tool in (raw_tools or [])
                if isinstance(tool, dict) and tool.get("id")
            ]
            return SnapshotListResult(
                snapshots=snapshots,
                provider_result=self.payload_schemas.snapshot_list_result.parse({}).model_dump(exclude_none=True),
            )

        agent_id = require_single_deployment_id(params, resource_label="snapshot")

        try:
            agent = await asyncio.to_thread(clients.agent.get_draft_by_id, agent_id)
        except Exception as exc:  # noqa: BLE001
            raise_as_deployment_error(
                exc,
                error_prefix=ErrorPrefix.LIST,
                log_msg="Unexpected error while listing wxO deployment snapshots",
            )

        if not agent or not isinstance(agent, dict):
            msg = f"Deployment '{agent_id}' not found."
            raise DeploymentNotFoundError(msg)

        tools: list[dict] = []
        requested_tool_ids = dedupe_list(agent.get("tools", []))
        if requested_tool_ids:
            try:
                tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, requested_tool_ids)
            except Exception as exc:  # noqa: BLE001
                raise_as_deployment_error(
                    exc,
                    error_prefix=ErrorPrefix.LIST,
                    log_msg="Unexpected error while listing wxO tools for snapshot extraction",
                )

        snapshots = [
            SnapshotItem(
                id=tool["id"],
                name=tool.get("name") or tool["id"],
                provider_data=self._validate_snapshot_item_provider_data(
                    {"connections": extract_langflow_connections_binding(tool)}
                ),
            )
            for tool in (tools or [])
            if isinstance(tool, dict) and tool.get("id")
        ]
        resolved_ids = {s.id for s in snapshots}
        stale_ids = [tid for tid in requested_tool_ids if tid not in resolved_ids]
        if stale_ids:
            logger.warning(
                "list_snapshots: agent '%s' references tool IDs that no longer exist on the provider: %s",
                agent_id,
                stale_ids,
            )

        return SnapshotListResult(
            snapshots=snapshots,
            provider_result=self.payload_schemas.snapshot_list_result.parse({"deployment_id": agent_id}).model_dump(
                exclude_none=True
            ),
        )