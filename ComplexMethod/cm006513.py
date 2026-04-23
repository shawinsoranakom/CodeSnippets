def _build_provider_operations(
        self,
        *,
        add_flows: list[WatsonxApiAddFlowItem] | None = None,
        upsert_flows: list[WatsonxApiUpsertFlowItem] | None = None,
        upsert_tools: list[WatsonxApiUpsertToolItem] | list[WatsonxApiCreateUpsertToolItem] | None = None,
        remove_flows: list[UUID] | None = None,
        remove_tools: list[str] | None = None,
        raw_name_by_flow_version_id: dict[UUID, str],
        flow_version_snapshot_id_map: dict[UUID, str] | None = None,
    ) -> list[AdapterPayload]:
        provider_operations: list[AdapterPayload] = []
        add_flows = add_flows or []
        upsert_flows = upsert_flows or []
        upsert_tools = upsert_tools or []
        remove_flows = remove_flows or []
        remove_tools = remove_tools or []

        # Create path flow semantics.
        for item in add_flows:
            flow_version_id = item.flow_version_id
            existing_tool_id = (flow_version_snapshot_id_map or {}).get(flow_version_id)
            if existing_tool_id:
                if item.app_ids:
                    provider_operations.append(
                        self._to_bind_existing_tool_provider_operation(
                            tool_id=existing_tool_id,
                            source_ref=str(flow_version_id),
                            app_ids=item.app_ids,
                        )
                    )
                else:
                    provider_operations.append(
                        self._to_attach_tool_provider_operation(
                            tool_id=existing_tool_id,
                            source_ref=str(flow_version_id),
                        )
                    )
                continue

            if flow_version_id not in raw_name_by_flow_version_id:
                msg = f"add_flows.flow_version_id not found: [{flow_version_id}]"
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
            if not item.app_ids:
                # Raw tool is still created via tools.raw_payloads;
                # no provider bind operation needed.
                continue
            provider_operations.append(
                self._to_bind_provider_operation(
                    raw_name=raw_name_by_flow_version_id[flow_version_id],
                    app_ids=item.app_ids,
                )
            )

        # Update path flow semantics.
        for item in upsert_flows:
            flow_version_id = item.flow_version_id
            existing_tool_id = (flow_version_snapshot_id_map or {}).get(flow_version_id)
            if existing_tool_id:
                if item.add_app_ids:
                    provider_operations.append(
                        self._to_bind_existing_tool_provider_operation(
                            tool_id=existing_tool_id,
                            source_ref=str(flow_version_id),
                            app_ids=item.add_app_ids,
                        )
                    )
                elif not item.remove_app_ids:
                    # Empty add/remove means ensure attached.
                    provider_operations.append(
                        self._to_attach_tool_provider_operation(
                            tool_id=existing_tool_id,
                            source_ref=str(flow_version_id),
                        )
                    )
                if item.remove_app_ids:
                    provider_operations.append(
                        self._to_unbind_provider_operation(
                            tool_id=existing_tool_id,
                            source_ref=str(flow_version_id),
                            app_ids=item.remove_app_ids,
                        )
                    )
                if item.tool_name:
                    provider_operations.append(
                        {
                            "op": "rename_tool",
                            "tool": {
                                "source_ref": str(flow_version_id),
                                "tool_id": existing_tool_id,
                            },
                            "new_name": _validate_tool_name(item.tool_name),
                        }
                    )
                continue

            if item.remove_app_ids:
                msg = (
                    "Cannot resolve provider snapshot ids for flow_version_ids "
                    f"in watsonx operations: [{flow_version_id}]"
                )
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
            if flow_version_id not in raw_name_by_flow_version_id:
                msg = f"upsert_flows.flow_version_id not found: [{flow_version_id}]"
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
            if item.add_app_ids:
                provider_operations.append(
                    self._to_bind_provider_operation(
                        raw_name=raw_name_by_flow_version_id[flow_version_id],
                        app_ids=item.add_app_ids,
                    )
                )

        # Update flow removals.
        for flow_version_id in remove_flows:
            if flow_version_snapshot_id_map is None or flow_version_id not in flow_version_snapshot_id_map:
                msg = (
                    "Cannot resolve provider snapshot ids for flow_version_ids "
                    f"in watsonx operations: [{flow_version_id}]"
                )
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
            provider_operations.append(
                self._to_remove_tool_provider_operation(
                    tool_id=flow_version_snapshot_id_map[flow_version_id],
                    source_ref=str(flow_version_id),
                )
            )

        # Tool-id-based semantics (create + update).
        for item in upsert_tools:
            tool_id = item.tool_id.strip()
            remove_app_ids = getattr(item, "remove_app_ids", []) or []
            if item.add_app_ids:
                provider_operations.append(
                    self._to_bind_existing_tool_provider_operation(
                        tool_id=tool_id,
                        source_ref=tool_id,
                        app_ids=item.add_app_ids,
                    )
                )
            elif not remove_app_ids:
                provider_operations.append(
                    self._to_attach_tool_provider_operation(
                        tool_id=tool_id,
                        source_ref=tool_id,
                    )
                )
            if remove_app_ids:
                provider_operations.append(
                    self._to_unbind_provider_operation(
                        tool_id=tool_id,
                        source_ref=tool_id,
                        app_ids=remove_app_ids,
                    )
                )

        for tool_id in remove_tools:
            normalized_tool_id = str(tool_id).strip()
            provider_operations.append(
                self._to_remove_tool_provider_operation(
                    tool_id=normalized_tool_id,
                    source_ref=normalized_tool_id,
                )
            )

        return provider_operations