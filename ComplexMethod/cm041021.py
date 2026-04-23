def get_service_name(resource):
    res_type = resource["Type"]
    parts = res_type.split("::")
    if len(parts) == 1:
        return None
    if "Cognito::IdentityPool" in res_type:
        return "cognito-identity"
    if res_type.endswith("Cognito::UserPool"):
        return "cognito-idp"
    if parts[-2] == "Cognito":
        return "cognito-idp"
    if parts[-2] == "Elasticsearch":
        return "es"
    if parts[-2] == "OpenSearchService":
        return "opensearch"
    if parts[-2] == "KinesisFirehose":
        return "firehose"
    if parts[-2] == "ResourceGroups":
        return "resource-groups"
    if parts[-2] == "CertificateManager":
        return "acm"
    if "ElasticLoadBalancing::" in res_type:
        return "elb"
    if "ElasticLoadBalancingV2::" in res_type:
        return "elbv2"
    if "ApplicationAutoScaling::" in res_type:
        return "application-autoscaling"
    if "MSK::" in res_type:
        return "kafka"
    if "Timestream::" in res_type:
        return "timestream-write"
    return parts[1].lower()