def resolve_ref(
    account_id: str,
    region_name: str,
    stack_name: str,
    resources: dict,
    parameters: dict[str, StackParameter],
    ref: str,
):
    """
    ref always needs to be a static string
    ref can be one of these:
    1. a pseudo-parameter (e.g. AWS::Region)
    2. a parameter
    3. the id of a resource (PhysicalResourceId
    """
    # pseudo parameter
    if ref == "AWS::Region":
        return region_name
    if ref == "AWS::Partition":
        return get_partition(region_name)
    if ref == "AWS::StackName":
        return stack_name
    if ref == "AWS::StackId":
        stack = find_stack(account_id, region_name, stack_name)
        if not stack:
            raise ValueError(f"No stack {stack_name} found")
        return stack.stack_id
    if ref == "AWS::AccountId":
        return account_id
    if ref == "AWS::NoValue":
        return PLACEHOLDER_AWS_NO_VALUE
    if ref == "AWS::NotificationARNs":
        # TODO!
        return {}
    if ref == "AWS::URLSuffix":
        return AWS_URL_SUFFIX

    # parameter
    if parameter := parameters.get(ref):
        parameter_type: str = parameter["ParameterType"]
        parameter_value = parameter.get("ResolvedValue") or parameter.get("ParameterValue")

        if "CommaDelimitedList" in parameter_type or parameter_type.startswith("List<"):
            return [p.strip() for p in parameter_value.split(",")]
        else:
            return parameter_value

    # resource
    resource = resources.get(ref)
    if not resource:
        raise Exception(
            f"Resource target for `Ref {ref}` could not be found. Is there a resource with name {ref} in your stack?"
        )

    return resources[ref].get("PhysicalResourceId")