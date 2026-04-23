def validate_function_name(function_name_or_arn: str, operation_type: str):
    function_name, *_ = function_locators_from_arn(function_name_or_arn)
    arn_name_pattern = ARN_NAME_PATTERN_CREATE
    max_length = 170

    if operation_type == "GetFunction" or operation_type == "Invoke":
        arn_name_pattern = ARN_NAME_PATTERN_GET
    elif operation_type == "CreateFunction":
        # https://docs.aws.amazon.com/lambda/latest/api/API_CreateFunction.html#lambda-CreateFunction-request-FunctionName
        if function_name == function_name_or_arn:  # only a function name
            max_length = 64
        else:  # full or partial ARN
            max_length = 140
    elif operation_type == "DeleteFunction":
        max_length = 140
        arn_name_pattern = ARN_NAME_PATTERN_GET

    validations = []
    if not AWS_FUNCTION_NAME_REGEX.match(function_name_or_arn) or not function_name:
        constraint = f"Member must satisfy regular expression pattern: {arn_name_pattern}"
        validation_msg = f"Value '{function_name_or_arn}' at 'functionName' failed to satisfy constraint: {constraint}"
        validations.append(validation_msg)
        if not operation_type == "CreateFunction":
            # Immediately raises rather than summarizing all validations, except for CreateFunction
            return validations

    if len(function_name_or_arn) > max_length:
        constraint = f"Member must have length less than or equal to {max_length}"
        validation_msg = f"Value '{function_name_or_arn}' at 'functionName' failed to satisfy constraint: {constraint}"
        validations.append(validation_msg)

    return validations