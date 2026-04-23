def _build_resource_failure_message(
    resource_type: str, status: AwsServicesSupportStatus | CfnResourceSupportStatus
) -> str:
    service_name = _get_service_name(resource_type) or "malformed"
    template = "Sorry, the {resource} resource in the {service} service is not supported."
    match status:
        case CloudFormationResourcesSupportAtRuntime.NOT_IMPLEMENTED:
            template = "Sorry, the {resource} resource (from the {service} service) is not supported by this version of LocalStack, but is available in the latest version."
        case CloudFormationResourcesSupportInLatest.NOT_SUPPORTED:
            template = "Sorry, the {resource} resource (from the {service} service) is not currently supported by LocalStack."
        case AwsServiceSupportAtRuntime.AVAILABLE_WITH_LICENSE_UPGRADE:
            template = "Sorry, the {service} service (for the {resource} resource) is not included within your LocalStack license, but is available in an upgraded license."
        case AwsServiceSupportAtRuntime.NOT_IMPLEMENTED:
            template = "The API for service {service} (for the {resource} resource) is either not included in your current license plan or has not yet been emulated by LocalStack."
        case AwsServicesSupportInLatest.NOT_SUPPORTED:
            template = "Sorry, the {service} (for the {resource} resource) service is not currently supported by LocalStack."
        case AwsServicesSupportInLatest.SUPPORTED_WITH_LICENSE_UPGRADE:
            template = "Sorry, the {service} service (for the {resource} resource) is not supported by this version of LocalStack, but is available in the latest version if you upgrade to the latest stable version."
    return template.format(
        resource=resource_type,
        service=service_name,
    )