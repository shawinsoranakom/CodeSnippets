def build_statement(
    partition: str,
    resource_arn: str,
    statement_id: str,
    action: str,
    principal: str,
    source_arn: str | None = None,
    source_account: str | None = None,
    principal_org_id: str | None = None,
    event_source_token: str | None = None,
    auth_type: FunctionUrlAuthType | None = None,
) -> dict[str, Any]:
    statement = {
        "Sid": statement_id,
        "Effect": "Allow",
        "Action": action,
        "Resource": resource_arn,
    }

    # See AWS service principals for comprehensive docs:
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
    # TODO: validate against actual list of IAM-supported AWS services (e.g., lambda.amazonaws.com)
    if principal.endswith(".amazonaws.com"):
        statement["Principal"] = {"Service": principal}
    elif is_aws_account(principal):
        statement["Principal"] = {"AWS": f"arn:{partition}:iam::{principal}:root"}
    # TODO: potentially validate against IAM?
    elif re.match(f"{ARN_PARTITION_REGEX}:iam:", principal):
        statement["Principal"] = {"AWS": principal}
    elif principal == "*":
        statement["Principal"] = principal
    # TODO: unclear whether above matching is complete?
    else:
        raise InvalidParameterValueException(
            "The provided principal was invalid. Please check the principal and try again.",
            Type="User",
        )

    condition = {}
    if auth_type:
        update = {"StringEquals": {"lambda:FunctionUrlAuthType": auth_type}}
        condition = merge_recursive(condition, update)

    if principal_org_id:
        update = {"StringEquals": {"aws:PrincipalOrgID": principal_org_id}}
        condition = merge_recursive(condition, update)

    if source_account:
        update = {"StringEquals": {"AWS:SourceAccount": source_account}}
        condition = merge_recursive(condition, update)

    if event_source_token:
        update = {"StringEquals": {"lambda:EventSourceToken": event_source_token}}
        condition = merge_recursive(condition, update)

    if source_arn:
        update = {"ArnLike": {"AWS:SourceArn": source_arn}}
        condition = merge_recursive(condition, update)

    if condition:
        statement["Condition"] = condition

    return statement