def _collect_operations() -> tuple[ServiceModel, OperationModel]:
    """
    Collects all service<>operation combinations to test.
    """
    service_catalog = get_service_catalog()
    for service_name in service_catalog.service_names:
        service = service_catalog.get(service_name)
        service_protocols = {service.protocol}
        if protocols := service.metadata.get("protocols"):
            service_protocols.update(protocols)

        for service_protocol in sorted(service_protocols):
            for operation_name in service.operation_names:
                # FIXME try to support more and more services, get these exclusions down!
                # Exclude all operations for the following, currently _not_ supported services
                if service.service_name in [
                    "bedrock-agent",
                    "bedrock-agentcore",
                    "bedrock-agentcore-control",
                    "bedrock-agent-runtime",
                    "bedrock-data-automation",
                    "bedrock-data-automation-runtime",
                    "chime",
                    "chime-sdk-identity",
                    "chime-sdk-media-pipelines",
                    "chime-sdk-meetings",
                    "chime-sdk-messaging",
                    "chime-sdk-voice",
                    "codecatalyst",
                    "connect",
                    "connect-contact-lens",
                    "connectcampaigns",
                    "connectcampaignsv2",
                    "greengrassv2",
                    "iot1click",
                    "iot1click-devices",
                    "iot1click-projects",
                    "ivs",
                    "ivs-realtime",
                    "kinesis-video-archived",
                    "kinesis-video-archived-media",
                    "kinesis-video-media",
                    "kinesis-video-signaling",
                    "kinesis-video-webrtc-storage",
                    "kinesisvideo",
                    "lex-models",
                    "lex-runtime",
                    "lexv2-models",
                    "lexv2-runtime",
                    "mailmanager",
                    "marketplace-catalog",
                    "marketplace-deployment",
                    "marketplace-reporting",
                    "personalize",
                    "personalize-events",
                    "personalize-runtime",
                    "pinpoint-sms-voice",
                    "qconnect",
                    "sagemaker-edge",
                    "sagemaker-featurestore-runtime",
                    "sagemaker-metrics",
                    "signin",
                    "signer",  # `signer` has conflicts with `signer-data` `GetRevocationStatus`
                    "signer-data",
                    "sms-voice",
                    "sso",
                    "sso-oidc",
                    "wisdom",
                    "workdocs",
                ]:
                    yield pytest.param(
                        service,
                        service_protocol,
                        service.operation_model(operation_name),
                        marks=pytest.mark.skip(
                            reason=f"{service.service_name} is currently not supported by the service router"
                        ),
                    )
                # Exclude services / operations which have ambiguities and where the service routing needs to resolve those
                elif (
                    service.service_name in ["docdb", "neptune"]  # maps to rds
                    or service.service_name in "timestream-write"  # maps to timestream-query
                    or (
                        service.service_name == "sesv2"
                        and operation_name == "PutEmailIdentityDkimSigningAttributes"
                    )
                ):
                    yield pytest.param(
                        service,
                        service_protocol,
                        service.operation_model(operation_name),
                        marks=pytest.mark.skip(
                            reason=f"{service.service_name} may differ due to ambiguities in the service specs"
                        ),
                    )
                else:
                    yield service, service_protocol, service.operation_model(operation_name)