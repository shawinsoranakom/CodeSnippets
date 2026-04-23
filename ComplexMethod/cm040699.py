def get_name_and_qualifier(
    function_arn_or_name: str, qualifier: str | None, context: RequestContext
) -> tuple[str, str | None]:
    """
    Takes a full or partial arn, or a name and a qualifier.

    :param function_arn_or_name: Given arn (or name)
    :param qualifier: A qualifier for the function (or None)
    :param context: Request context
    :return: tuple with (name, qualifier). Qualifier is none if missing
    :raises: `ResourceNotFoundException` when the context's region differs from the ARN's region
    :raises: `AccessDeniedException` when the context's account ID differs from the ARN's account ID
    :raises: `ValidationExcpetion` when a function ARN/name or qualifier fails validation checks
    :raises: `InvalidParameterValueException` when a qualified arn is provided and the qualifier does not match (but is given)
    """
    function_name, arn_qualifier, account, region = function_locators_from_arn(function_arn_or_name)
    operation_type = context.operation.name

    if operation_type not in _supported_resource_based_operations:
        if account and account != context.account_id:
            raise AccessDeniedException(None)

    # TODO: should this only run if operation type is unsupported?
    if region and region != context.region:
        raise ResourceNotFoundException(
            f"Functions from '{region}' are not reachable in this region ('{context.region}')",
            Type="User",
        )

    validation_errors = []
    if function_arn_or_name:
        validation_errors.extend(validate_function_name(function_arn_or_name, operation_type))

    if qualifier:
        validation_errors.extend(validate_qualifier(qualifier))

    is_only_function_name = function_arn_or_name == function_name
    if validation_errors:
        message = construct_validation_exception_message(validation_errors)
        # Edge-case where the error type is not ValidationException
        if (
            operation_type == "CreateFunction"
            and is_only_function_name
            and arn_qualifier is None
            and region is None
        ):  # just name OR partial
            raise InvalidParameterValueException(message=message, Type="User")
        raise CommonServiceException(message=message, code="ValidationException")

    if qualifier and arn_qualifier and arn_qualifier != qualifier:
        raise InvalidParameterValueException(
            "The derived qualifier from the function name does not match the specified qualifier.",
            Type="User",
        )

    qualifier = qualifier or arn_qualifier
    return function_name, qualifier