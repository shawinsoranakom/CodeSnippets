async def rollback_provider_create(
    *,
    deployment_adapter: DeploymentServiceProtocol,
    provider_id: UUID,
    resource_id: object,
    provider_result: Any | None = None,
    allow_delete_fallback: bool = True,
    user_id: UUID,
    db: DbSession,
) -> None:
    """Best-effort compensating cleanup after a failed DB commit on create."""
    # TODO: Add this method to the deployment service protocol.
    rollback_create_result = getattr(deployment_adapter, "rollback_create_result", None)
    if provider_result is not None and callable(rollback_create_result):
        try:
            with deployment_provider_scope(provider_id):
                await rollback_create_result(
                    deployment_id=str(resource_id),
                    provider_result=provider_result,
                    user_id=user_id,
                    db=db,
                )
        except Exception:  # noqa: BLE001
            if allow_delete_fallback:
                logger.warning(
                    "Extended rollback failed for provider resource %s on provider account %s; "
                    "falling back to basic delete.",
                    resource_id,
                    provider_id,
                    exc_info=True,
                )
            else:
                logger.warning(
                    "Extended rollback failed for existing provider resource %s on provider account %s; "
                    "skipping delete fallback.",
                    resource_id,
                    provider_id,
                    exc_info=True,
                )
                return
        else:
            logger.info(
                "Rolled back provider create result for resource %s on provider account %s after DB commit failure.",
                resource_id,
                provider_id,
            )
            return
    if not allow_delete_fallback:
        logger.warning(
            "Skipping delete fallback for existing provider resource %s on provider account %s; "
            "provider side-effects may require manual cleanup.",
            resource_id,
            provider_id,
        )
        return
    try:
        with deployment_provider_scope(provider_id):
            await deployment_adapter.delete(
                deployment_id=str(resource_id),
                user_id=user_id,
                db=db,
            )
        logger.info(
            "Rolled back provider resource %s on provider account %s after DB commit failure.",
            resource_id,
            provider_id,
        )
    except Exception:  # noqa: BLE001
        logger.critical(
            "Rollback failed: provider resource %s may be orphaned on provider account %s. "
            "Manual cleanup may be required.",
            resource_id,
            provider_id,
            exc_info=True,
        )