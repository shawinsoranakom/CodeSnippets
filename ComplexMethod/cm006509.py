async def _resolve_provider_payload_from_create_api(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        db: AsyncSession,
        payload: DeploymentCreateRequest,
        slot: PayloadSlot | None,
        slot_name: str,
    ) -> AdapterPayload:
        if payload.provider_data is None:
            msg = "Watsonx create requires provider_data operations."
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

        api_provider_payload: WatsonxApiDeploymentCreatePayload = self._parse_api_payload_slot(
            slot=self.api_payloads.deployment_create,
            slot_name="deployment_create",
            raw=payload.provider_data,
        )
        flow_version_ids = list(dict.fromkeys(item.flow_version_id for item in api_provider_payload.add_flows))
        flow_artifacts = await build_project_scoped_flow_artifacts_from_flow_versions(
            db=db,
            user_id=user_id,
            project_id=project_id,
            reference_ids=flow_version_ids,
        )
        # Start with flow names as defaults, then let user-provided tool_name
        # overrides replace them. Validation runs on the final map so that an
        # invalid flow name doesn't block a user who provided a valid custom
        # tool_name for that flow.
        raw_name_by_flow_version_id: dict[UUID, str] = {
            flow_version_id: artifact.name for flow_version_id, artifact in flow_artifacts
        }
        for item in api_provider_payload.add_flows:
            if item.tool_name:
                raw_name_by_flow_version_id[item.flow_version_id] = item.tool_name
        for fv_id, name in raw_name_by_flow_version_id.items():
            raw_name_by_flow_version_id[fv_id] = _validate_tool_name(name)
        provider_operations = self._build_provider_operations(
            add_flows=api_provider_payload.add_flows,
            upsert_tools=api_provider_payload.upsert_tools,
            raw_name_by_flow_version_id=raw_name_by_flow_version_id,
        )
        if slot is None:
            msg = f"Watsonx {slot_name} payload slot is not configured."
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
        try:
            return slot.apply(
                self._build_provider_payload_body(
                    llm=api_provider_payload.llm,
                    raw_tool_payloads=[
                        artifact.model_copy(
                            update={
                                "name": raw_name_by_flow_version_id[flow_version_id],
                                "provider_data": self.util_create_flow_artifact_provider_data(
                                    project_id=project_id,
                                    flow_version_id=flow_version_id,
                                ).model_dump(exclude_none=True),
                            }
                        ).model_dump(exclude_none=True)
                        for flow_version_id, artifact in flow_artifacts
                    ],
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