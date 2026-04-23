def get_domain_status(
    domain_key: DomainKey, deleted=False, request: CreateDomainRequest | None = None
) -> DomainStatus:
    parsed_arn = parse_arn(domain_key.arn)
    store = OpensearchProvider.get_store(parsed_arn["account"], parsed_arn["region"])
    stored_status: DomainStatus = (
        store.opensearch_domains.get(domain_key.domain_name) or DomainStatus()
    )
    cluster_cfg = stored_status.get("ClusterConfig") or {}
    default_cfg = DEFAULT_OPENSEARCH_CLUSTER_CONFIG
    if request:
        stored_status = deepcopy(stored_status)
        stored_status.update(request)
        default_cfg.update(request.get("ClusterConfig", {}))

    autotune_options = stored_status.get("AutoTuneOptions") or deepcopy(DEFAULT_AUTOTUNE_OPTIONS)
    if request and (request_options := request.get("AutoTuneOptions")):
        desired_state = request_options.get("DesiredState") or AutoTuneDesiredState.ENABLED
        state = (
            AutoTuneState.ENABLED
            if desired_state == AutoTuneDesiredState.ENABLED
            else AutoTuneState.DISABLED
        )
        autotune_options = AutoTuneOptionsOutput(
            State=state,
            UseOffPeakWindow=request_options.get(
                "UseOffPeakWindow", autotune_options.get("UseOffPeakWindow", False)
            ),
        )
    stored_status["AutoTuneOptions"] = autotune_options

    domain_processing_status = stored_status.get("DomainProcessingStatus", None)
    processing = stored_status.get("Processing", True)
    if deleted:
        domain_processing_status = DomainProcessingStatusType.Deleting
        processing = True

    new_status = DomainStatus(
        ARN=domain_key.arn,
        Created=True,
        Deleted=deleted,
        DomainProcessingStatus=domain_processing_status,
        Processing=processing,
        DomainId=f"{domain_key.account}/{domain_key.domain_name}",
        DomainName=domain_key.domain_name,
        ClusterConfig=ClusterConfig(
            DedicatedMasterCount=cluster_cfg.get(
                "DedicatedMasterCount", default_cfg["DedicatedMasterCount"]
            ),
            DedicatedMasterEnabled=cluster_cfg.get(
                "DedicatedMasterEnabled", default_cfg["DedicatedMasterEnabled"]
            ),
            DedicatedMasterType=cluster_cfg.get(
                "DedicatedMasterType", default_cfg["DedicatedMasterType"]
            ),
            InstanceCount=cluster_cfg.get("InstanceCount", default_cfg["InstanceCount"]),
            InstanceType=cluster_cfg.get("InstanceType", default_cfg["InstanceType"]),
            ZoneAwarenessEnabled=cluster_cfg.get(
                "ZoneAwarenessEnabled", default_cfg["ZoneAwarenessEnabled"]
            ),
            WarmEnabled=False,
            ColdStorageOptions=ColdStorageOptions(Enabled=False),
        ),
        EngineVersion=stored_status.get("EngineVersion") or OPENSEARCH_DEFAULT_VERSION,
        Endpoint=stored_status.get("Endpoint", None),
        EBSOptions=stored_status.get("EBSOptions")
        or EBSOptions(EBSEnabled=True, VolumeType=VolumeType.gp2, VolumeSize=10, Iops=0),
        CognitoOptions=CognitoOptions(Enabled=False),
        UpgradeProcessing=False,
        AccessPolicies=stored_status.get("AccessPolicies", ""),
        SnapshotOptions=SnapshotOptions(AutomatedSnapshotStartHour=0),
        EncryptionAtRestOptions=EncryptionAtRestOptions(Enabled=False),
        NodeToNodeEncryptionOptions=NodeToNodeEncryptionOptions(Enabled=False),
        AdvancedOptions={
            "override_main_response_version": "false",
            "rest.action.multi.allow_explicit_index": "true",
            **stored_status.get("AdvancedOptions", {}),
        },
        ServiceSoftwareOptions=ServiceSoftwareOptions(
            CurrentVersion="",
            NewVersion="",
            UpdateAvailable=False,
            Cancellable=False,
            UpdateStatus=DeploymentStatus.COMPLETED,
            Description="There is no software update available for this domain.",
            AutomatedUpdateDate=datetime.fromtimestamp(0, tz=UTC),
            OptionalDeployment=True,
        ),
        DomainEndpointOptions=stored_status.get("DomainEndpointOptions")
        or DEFAULT_OPENSEARCH_DOMAIN_ENDPOINT_OPTIONS,
        AdvancedSecurityOptions=AdvancedSecurityOptions(
            Enabled=False, InternalUserDatabaseEnabled=False
        ),
        AutoTuneOptions=AutoTuneOptionsOutput(
            State=stored_status.get("AutoTuneOptions", {}).get("State"),
            UseOffPeakWindow=autotune_options.get("UseOffPeakWindow", False),
        ),
    )
    return new_status