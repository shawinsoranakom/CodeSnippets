def execute_macro(
    account_id: str,
    region_name: str,
    parsed_template: dict,
    macro: dict,
    stack_parameters: dict,
    transformation_parameters: dict,
    is_intrinsic=False,
) -> str:
    macro_definition = get_cloudformation_store(account_id, region_name).macros.get(macro["Name"])
    if not macro_definition:
        raise FailedTransformationException(
            macro["Name"], f"Transformation {macro['Name']} is not supported."
        )

    formatted_stack_parameters = {}
    for key, value in stack_parameters.items():
        # TODO: we want to support other types of parameters
        parameter_value = value.get("ParameterValue")
        if value.get("ParameterType") == "CommaDelimitedList" and isinstance(parameter_value, str):
            formatted_stack_parameters[key] = parameter_value.split(",")
        else:
            formatted_stack_parameters[key] = parameter_value

    transformation_id = f"{account_id}::{macro['Name']}"
    event = {
        "region": region_name,
        "accountId": account_id,
        "fragment": parsed_template,
        "transformId": transformation_id,
        "params": transformation_parameters,
        "requestId": long_uid(),
        "templateParameterValues": formatted_stack_parameters,
    }

    client = connect_to(aws_access_key_id=account_id, region_name=region_name).lambda_
    try:
        invocation = client.invoke(
            FunctionName=macro_definition["FunctionName"], Payload=json.dumps(event)
        )
    except ClientError:
        LOG.error(
            "client error executing lambda function '%s' with payload '%s'",
            macro_definition["FunctionName"],
            json.dumps(event),
        )
        raise
    if invocation.get("StatusCode") != 200 or invocation.get("FunctionError") == "Unhandled":
        raise FailedTransformationException(
            transformation=macro["Name"],
            message=f"Received malformed response from transform {transformation_id}. Rollback requested by user.",
        )
    result = json.loads(invocation["Payload"].read())

    if result.get("status") != "success":
        error_message = result.get("errorMessage")
        message = (
            f"Transform {transformation_id} failed with: {error_message}. Rollback requested by user."
            if error_message
            else f"Transform {transformation_id} failed without an error message.. Rollback requested by user."
        )
        raise FailedTransformationException(transformation=macro["Name"], message=message)

    if not isinstance(result.get("fragment"), dict) and not is_intrinsic:
        raise FailedTransformationException(
            transformation=macro["Name"],
            message="Template format error: unsupported structure.. Rollback requested by user.",
        )

    return result.get("fragment")