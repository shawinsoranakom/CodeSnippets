async def update_snapshot(
        self,
        *,
        user_id: IdLike,
        db: AsyncSession,
        snapshot_id: str,
        flow_artifact: BaseFlowArtifact,
    ) -> SnapshotUpdateResult:
        """Replace an existing snapshot's artifact content.

        This is a content-only mutation -- it re-uploads the artifact zip
        without touching the tool's name, metadata, or connection bindings.

        The tool name is fetched from wxO at call time, not derived from the
        Langflow flow name. This is intentional: the user may have set a
        custom tool name during initial deployment, or renamed the tool
        directly in the wxO console. Either way, the provider is the source
        of truth for the tool name.

        **Edge cases:**

        * **Tool renamed in wxO console** — The new name is picked up
          automatically on the next update since we always fetch it fresh.
          Langflow never stores the tool name locally.
        * **Tool deleted in wxO** — ``get_drafts_by_ids`` returns empty
          and we raise ``InvalidContentError`` before any mutation.
        * **Tool exists but name is empty/null** — Defensive check raises
          ``InvalidContentError`` rather than passing an empty name to the
          ADK, which would produce a cryptic validation error.
        * **Race condition (rename between fetch and upload)** — The
          artifact zip will contain the name as of the fetch. The tool's
          API-level name (set by wxO, not by the artifact) is unaffected
          by the zip contents, so this is harmless.
        * **Tool deleted + recreated with same name** — The new tool has
          a different ``tool_id``.  Our attachment still references the
          old (deleted) ID, so ``get_drafts_by_ids`` returns nothing and
          we fail with ``InvalidContentError``.  The user must re-deploy
          (or update the agent) to bind the new tool — we never silently
          adopt an unrelated tool just because the name matches.

        **Identity model:** we track tools by immutable ``tool_id``, not
        by name.  A rename preserves identity; a delete+recreate does not.

        **Blast-radius boundary:** callers must verify that ``snapshot_id``
        is tracked by a Langflow attachment record before calling this
        method; this prevents accidental overwrites of externally managed
        WXO tools.
        """
        from ibm_watsonx_orchestrate_core.types.tools.langflow_tool import (
            create_langflow_tool as _create_langflow_tool,
        )

        from langflow.utils.version import get_version_info

        clients = await self._get_provider_clients(user_id=user_id, db=db)

        # Fetch the existing tool to preserve its wxO name — the tool may have
        # been deployed with a custom name that differs from the Langflow flow
        # name, and we must not overwrite it with the flow name.
        existing_tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, [snapshot_id])
        if not existing_tools or not isinstance(existing_tools[0], dict):
            msg = f"Snapshot tool '{snapshot_id}' not found in provider."
            raise InvalidContentError(message=msg)
        existing_tool_name = str(existing_tools[0].get("name") or "").strip()
        if not existing_tool_name:
            msg = f"Snapshot tool '{snapshot_id}' exists but has no name. Cannot update artifact."
            raise InvalidContentError(message=msg)
        logger.debug("update_snapshot: snapshot_id='%s', existing tool name='%s'", snapshot_id, existing_tool_name)

        flow_definition = flow_artifact.model_dump(exclude={"provider_data"})
        flow_id = flow_definition.get("id")
        if flow_id is None:
            msg = "flow_definition must have an id"
            raise ValueError(msg)
        flow_definition["id"] = str(flow_id)
        flow_definition["name"] = existing_tool_name
        if not flow_definition.get("last_tested_version"):
            detected_version = (get_version_info() or {}).get("version")
            if detected_version:
                flow_definition["last_tested_version"] = detected_version

        tool = _create_langflow_tool(
            tool_definition=flow_definition,
            connections={},
            show_details=True,
        )

        artifact_bytes = build_langflow_artifact_bytes(
            tool=tool,
            flow_definition=flow_definition,
        )
        await asyncio.to_thread(
            upload_tool_artifact_bytes,
            clients,
            tool_id=snapshot_id,
            artifact_bytes=artifact_bytes,
        )
        return SnapshotUpdateResult(snapshot_id=snapshot_id)