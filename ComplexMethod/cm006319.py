async def update(
        self,
        *,
        user_id: IdLike,
        deployment_id: IdLike,
        deployment_type: DeploymentType | None = None,  # noqa: ARG002
        payload: DeploymentUpdate,
        db: AsyncSession,
    ) -> DeploymentUpdateResult:
        """Update deployment metadata and provider-driven tool/config operations."""
        try:
            clients = await self._get_provider_clients(user_id=user_id, db=db)
            agent_id = _normalize_and_validate_id(str(deployment_id), field_name="deployment_id")

            agent = await asyncio.to_thread(clients.agent.get_draft_by_id, agent_id)

            if not agent:
                msg = f"Deployment '{agent_id}' not found."
                raise DeploymentNotFoundError(msg)

            validate_provider_update_request_sections(payload)
            provider_update: WatsonxDeploymentUpdatePayload | None = None
            if payload.provider_data is not None:
                provider_update = self._parse_provider_payload(
                    slot=self.payload_schemas.deployment_update,
                    slot_name="deployment_update",
                    provider_data=payload.provider_data,
                    error_prefix=ErrorPrefix.UPDATE,
                )
            # base agent payload to build for final update call
            update_payload: dict[str, Any] = build_update_payload_from_spec(
                payload.spec,
                llm=provider_update.llm if provider_update is not None else None,
            )

            if payload.provider_data is None or not (provider_update is not None and provider_update.has_tool_work):
                if not update_payload:
                    msg = "provider_data is required when update operations do not include spec changes."
                    raise InvalidContentError(message=msg)
                await retry_create(
                    asyncio.to_thread,
                    clients.agent.update,
                    agent_id,
                    update_payload,
                )
                return DeploymentUpdateResult[WatsonxDeploymentUpdateResultData](
                    id=deployment_id, provider_result=WatsonxDeploymentUpdateResultData()
                )

            provider_plan = build_provider_update_plan(
                agent=agent,
                provider_update=provider_update,
            )

            apply_result = await apply_provider_update_plan_with_rollback(
                clients=clients,
                user_id=user_id,
                db=db,
                agent_id=agent_id,
                agent=agent,
                update_payload=update_payload,
                plan=provider_plan,
            )

            return DeploymentUpdateResult[WatsonxDeploymentUpdateResultData](
                id=deployment_id,
                provider_result=self.payload_schemas.deployment_update_result.apply(
                    WatsonxDeploymentUpdateResultData(
                        created_app_ids=apply_result.created_app_ids,
                        created_snapshot_ids=apply_result.created_snapshot_ids,
                        added_snapshot_ids=apply_result.added_snapshot_ids,
                        created_snapshot_bindings=apply_result.created_snapshot_bindings,
                        added_snapshot_bindings=apply_result.added_snapshot_bindings,
                        removed_snapshot_bindings=apply_result.removed_snapshot_bindings,
                        referenced_snapshot_bindings=apply_result.referenced_snapshot_bindings,
                    )
                ),
            )

        except (ClientAPIException, HTTPException) as exc:
            raise_as_deployment_error(
                exc,
                error_prefix=ErrorPrefix.UPDATE,
                log_msg="Unexpected provider error during wxO deployment update",
            )
        except (
            AuthenticationError,
            AuthorizationError,
            DeploymentNotFoundError,
            InvalidContentError,
            InvalidDeploymentOperationError,
            ResourceConflictError,
        ):
            raise
        except Exception as exc:
            logger.exception("Unexpected error during wxO deployment update")
            msg = f"{ErrorPrefix.UPDATE.value} Please check server logs for details."
            raise DeploymentError(message=msg, error_code="deployment_error") from exc