def map_config_out(
    version: "FunctionVersion",
    return_qualified_arn: bool = False,
    return_update_status: bool = True,
    alias_name: str | None = None,
) -> FunctionConfiguration:
    """map function version to function configuration"""

    # handle optional entries that shouldn't be rendered at all if not present
    optional_kwargs = {}
    if return_update_status:
        optional_kwargs.update(map_update_status_config(version))
    optional_kwargs.update(map_state_config(version))

    if version.config.architectures:
        optional_kwargs["Architectures"] = version.config.architectures

    if version.config.dead_letter_arn:
        optional_kwargs["DeadLetterConfig"] = DeadLetterConfig(
            TargetArn=version.config.dead_letter_arn
        )

    if version.config.vpc_config:
        optional_kwargs["VpcConfig"] = VpcConfigResponse(
            VpcId=version.config.vpc_config.vpc_id,
            SubnetIds=version.config.vpc_config.subnet_ids,
            SecurityGroupIds=version.config.vpc_config.security_group_ids,
        )

    if version.config.environment is not None:
        optional_kwargs["Environment"] = EnvironmentResponse(
            Variables=version.config.environment
        )  # TODO: Errors key?

    if version.config.layers:
        optional_kwargs["Layers"] = [
            {"Arn": layer.layer_version_arn, "CodeSize": layer.code.code_size}
            for layer in version.config.layers
        ]
    if version.config.image_config:
        image_config = ImageConfig()
        if version.config.image_config.command:
            image_config["Command"] = version.config.image_config.command
        if version.config.image_config.entrypoint:
            image_config["EntryPoint"] = version.config.image_config.entrypoint
        if version.config.image_config.working_directory:
            image_config["WorkingDirectory"] = version.config.image_config.working_directory
        if image_config:
            optional_kwargs["ImageConfigResponse"] = ImageConfigResponse(ImageConfig=image_config)
    if version.config.code:
        optional_kwargs["CodeSize"] = version.config.code.code_size
        optional_kwargs["CodeSha256"] = version.config.code.code_sha256
    elif version.config.image:
        optional_kwargs["CodeSize"] = 0
        optional_kwargs["CodeSha256"] = version.config.image.code_sha256

    if version.config.capacity_provider_config:
        optional_kwargs["CapacityProviderConfig"] = version.config.capacity_provider_config
        data = json.dumps(version.config.capacity_provider_config, sort_keys=True).encode("utf-8")
        config_sha_256 = hashlib.sha256(data).hexdigest()
        optional_kwargs["ConfigSha256"] = config_sha_256

    # output for an alias qualifier is completely the same except for the returned ARN
    if alias_name:
        function_arn = f"{':'.join(version.id.qualified_arn().split(':')[:-1])}:{alias_name}"
    else:
        function_arn = (
            version.id.qualified_arn() if return_qualified_arn else version.id.unqualified_arn()
        )

    func_conf = FunctionConfiguration(
        RevisionId=version.config.revision_id,
        FunctionName=version.id.function_name,
        FunctionArn=function_arn,
        LastModified=version.config.last_modified,
        Version=version.id.qualifier,
        Description=version.config.description,
        Role=version.config.role,
        Timeout=version.config.timeout,
        Runtime=version.config.runtime,
        Handler=version.config.handler,
        MemorySize=version.config.memory_size,
        PackageType=version.config.package_type,
        TracingConfig=TracingConfig(Mode=version.config.tracing_config_mode),
        EphemeralStorage=EphemeralStorage(Size=version.config.ephemeral_storage.size),
        SnapStart=version.config.snap_start,
        RuntimeVersionConfig=version.config.runtime_version_config,
        LoggingConfig=version.config.logging_config,
        **optional_kwargs,
    )
    return func_conf