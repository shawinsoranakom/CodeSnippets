async def resolve_variable_value(
    variable_name: str,
    *,
    user_id: UUID | str,
    db: AsyncSession,
    optional: bool = False,
    default_value: str | None = None,
) -> str:
    variable_service = get_variable_service()
    if variable_service is None:
        msg = "Variable service is not available."
        raise CredentialResolutionError(message=msg)
    try:
        value = await variable_service.get_variable(
            user_id=user_id,
            name=variable_name,
            field="value",
            session=db,
        )
        if value is not None:
            return value
    except CredentialResolutionError:
        raise
    except Exception as exc:
        if not optional:
            msg = "Failed to resolve a credential variable for the watsonx Orchestrate deployment provider."
            raise CredentialResolutionError(message=msg) from exc
    if optional:
        return default_value or ""
    msg = (
        "Failed to find a necessary credential for the "
        "watsonx Orchestrate deployment provider. "
        "Please ensure all credentials are provided and valid."
    )
    raise CredentialResolutionError(message=msg)