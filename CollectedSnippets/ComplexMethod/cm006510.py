async def resolve_deployment_update(
        self,
        *,
        user_id: UUID,
        deployment_db_id: UUID,
        db: AsyncSession,
        payload: DeploymentUpdateRequest,
    ) -> AdapterDeploymentUpdate:
        adapter_spec = (
            BaseDeploymentDataUpdate(
                name=payload.name,
                description=payload.description,
            )
            if payload.name is not None or payload.description is not None
            else None
        )
        if payload.provider_data is None:  # pure metadata update, e.g., name, description
            return AdapterDeploymentUpdate(spec=adapter_spec, provider_data=None)

        api_provider_payload: WatsonxApiDeploymentUpdatePayload = self._parse_api_payload_slot(
            slot=self.api_payloads.deployment_update,
            slot_name="deployment_update",
            raw=payload.provider_data,
        )
        ordered_flow_version_ids = list(
            dict.fromkeys(
                item.flow_version_id
                for item in api_provider_payload.upsert_flows
                if item.add_app_ids or not item.remove_app_ids
            )
        )
        flow_artifacts = await build_flow_artifacts_from_flow_versions(
            db=db,
            user_id=user_id,
            deployment_db_id=deployment_db_id,
            flow_version_ids=ordered_flow_version_ids,
        )
        # Start with normalized flow names as defaults, then let user-provided
        # tool_name overrides replace them. Validation runs on the final map
        # so that an invalid flow name doesn't block a user who provided a
        # valid custom tool_name for that flow.
        raw_name_by_flow_version_id: dict[UUID, str] = {
            flow_version_id: artifact.name for flow_version_id, _version_number, _project_id, artifact in flow_artifacts
        }
        # Override with user-provided tool names when present
        for item in api_provider_payload.upsert_flows:
            if item.tool_name and item.flow_version_id in raw_name_by_flow_version_id:
                raw_name_by_flow_version_id[item.flow_version_id] = item.tool_name
        for fv_id, name in raw_name_by_flow_version_id.items():
            raw_name_by_flow_version_id[fv_id] = _validate_tool_name(name)
        raw_payloads = [
            artifact.model_copy(
                update={
                    "name": raw_name_by_flow_version_id[flow_version_id],
                    "provider_data": self.util_create_flow_artifact_provider_data(
                        project_id=project_id,
                        flow_version_id=flow_version_id,
                    ).model_dump(exclude_none=True),
                }
            )
            for flow_version_id, _version_number, project_id, artifact in flow_artifacts
        ]

        upsert_fv_ids = list(dict.fromkeys(item.flow_version_id for item in api_provider_payload.upsert_flows))
        remove_fv_ids = list(dict.fromkeys(api_provider_payload.remove_flows))
        all_fv_ids = list(dict.fromkeys(upsert_fv_ids + remove_fv_ids))
        flow_version_snapshot_id_map = await self._lookup_snapshot_ids(
            user_id=user_id,
            deployment_db_id=deployment_db_id,
            db=db,
            flow_version_ids=all_fv_ids,
        )
        strict_fv_ids = list(
            dict.fromkeys(
                [item.flow_version_id for item in api_provider_payload.upsert_flows if item.remove_app_ids]
                + remove_fv_ids
            )
        )
        missing_strict = [str(fv) for fv in strict_fv_ids if fv not in flow_version_snapshot_id_map]
        if missing_strict:
            msg = f"Cannot resolve provider snapshot ids for flow_version_ids in watsonx operations: {missing_strict}"
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

        reused_fv_ids = {
            item.flow_version_id
            for item in api_provider_payload.upsert_flows
            if (item.add_app_ids or not item.remove_app_ids) and item.flow_version_id in flow_version_snapshot_id_map
        }
        filtered_raw_payloads = (
            [
                raw_payload
                for (flow_version_id, _version_number, _project_id, _artifact), raw_payload in zip(
                    flow_artifacts, raw_payloads, strict=True
                )
                if flow_version_id not in reused_fv_ids
            ]
            if reused_fv_ids
            else raw_payloads
        )

        provider_operations = self._build_provider_operations(
            upsert_flows=api_provider_payload.upsert_flows,
            upsert_tools=api_provider_payload.upsert_tools,
            remove_flows=api_provider_payload.remove_flows,
            remove_tools=api_provider_payload.remove_tools,
            raw_name_by_flow_version_id=raw_name_by_flow_version_id,
            flow_version_snapshot_id_map=flow_version_snapshot_id_map,
        )

        update_slot = WXO_ADAPTER_PAYLOAD_SCHEMAS.deployment_update
        if update_slot is None:
            msg = "Watsonx deployment_update payload slot is not configured."
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
        try:
            provider_payload: AdapterPayload = update_slot.apply(
                self._build_provider_payload_body(
                    llm=api_provider_payload.llm,
                    raw_tool_payloads=[artifact.model_dump(exclude_none=True) for artifact in filtered_raw_payloads],
                    connections=api_provider_payload.connections,
                    operations=provider_operations,
                )
            )
        except AdapterPayloadValidationError as exc:
            first_error = exc.error.errors()[0] if exc.error.errors() else {}
            detail = str(first_error.get("msg") or exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid provider_data payload: {detail}",
            ) from exc
        return AdapterDeploymentUpdate(
            spec=adapter_spec,
            provider_data=provider_payload,
        )