def handle_adapter_errors(*, mapper: BaseDeploymentMapper | None = None):
    """Map deployment adapter exceptions to appropriate HTTP responses.

    Domain exceptions (subclasses of :class:`DeploymentServiceError`) are
    mapped via :func:`http_status_for_deployment_error` in the shared
    ``lfx.services.adapters.deployment.exceptions`` module.  Non-domain
    exceptions (``NotImplementedError``, ``ValueError``, etc.) are handled
    as special cases here.
    """
    try:
        yield
    except DeploymentServiceError as exc:
        http_status = http_status_for_deployment_error(exc)
        detail = exc.message
        if isinstance(exc, ResourceConflictError) and mapper is not None:
            detail = mapper.format_conflict_detail(
                exc.message,
                resource=exc.resource,
                resource_name=exc.resource_name,
            )
        logger.exception("Adapter error (status=%s): %s", http_status, detail)
        raise HTTPException(
            status_code=http_status,
            detail=detail,
        ) from exc
    except NotImplementedError as exc:
        logger.exception("Adapter not-implemented error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="This operation is not supported by the deployment provider.",
        ) from exc
    except ValueError as exc:
        logger.exception("Adapter value error: %s", exc)
        raise_http_for_value_error(exc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled adapter error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while communicating with the deployment provider.",
        ) from exc