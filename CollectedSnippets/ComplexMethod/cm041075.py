def _get_service_name(resource_type: str) -> str | None:
    parts = resource_type.split("::")
    if len(parts) == 1:
        return None

    match parts:
        case _ if "Cognito::IdentityPool" in resource_type:
            return "cognito-identity"
        case [*_, "Cognito", "UserPool"]:
            return "cognito-idp"
        case [*_, "Cognito", _]:
            return "cognito-idp"
        case [*_, "Elasticsearch", _]:
            return "es"
        case [*_, "OpenSearchService", _]:
            return "opensearch"
        case [*_, "KinesisFirehose", _]:
            return "firehose"
        case [*_, "ResourceGroups", _]:
            return "resource-groups"
        case [*_, "CertificateManager", _]:
            return "acm"
        case _ if "ElasticLoadBalancing::" in resource_type:
            return "elb"
        case _ if "ElasticLoadBalancingV2::" in resource_type:
            return "elbv2"
        case _ if "ApplicationAutoScaling::" in resource_type:
            return "application-autoscaling"
        case _ if "MSK::" in resource_type:
            return "kafka"
        case _ if "Timestream::" in resource_type:
            return "timestream-write"
        case [_, service, *_]:
            return service.lower()