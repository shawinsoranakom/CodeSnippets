def resolve_pseudo_parameter(
    account_id: str, region_name: str, pseudo_parameter: str, stack_name: str
) -> Any:
    """
    TODO: this function needs access to more stack context
    """
    # pseudo parameters
    match pseudo_parameter:
        case "AWS::Region":
            return region_name
        case "AWS::Partition":
            return "aws"
        case "AWS::StackName":
            return stack_name
        case "AWS::StackId":
            # TODO return proper stack id!
            return stack_name
        case "AWS::AccountId":
            return account_id
        case "AWS::NoValue":
            return PLACEHOLDER_AWS_NO_VALUE
        case "AWS::NotificationARNs":
            # TODO!
            return {}
        case "AWS::URLSuffix":
            return AWS_URL_SUFFIX