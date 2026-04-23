def create_function(
        self,
        context: RequestContext,
        request: CreateFunctionRequest,
    ) -> FunctionConfiguration:
        context_region = context.region
        context_account_id = context.account_id

        zip_file = (request.get("Code") or {}).get("ZipFile")
        if zip_file and len(zip_file) > config.LAMBDA_LIMITS_CODE_SIZE_ZIPPED:
            raise RequestEntityTooLargeException(
                f"Zipped size must be smaller than {config.LAMBDA_LIMITS_CODE_SIZE_ZIPPED} bytes"
            )

        if context.request.content_length > config.LAMBDA_LIMITS_CREATE_FUNCTION_REQUEST_SIZE:
            raise RequestEntityTooLargeException(
                f"Request must be smaller than {config.LAMBDA_LIMITS_CREATE_FUNCTION_REQUEST_SIZE} bytes for the CreateFunction operation"
            )

        if architectures := request.get("Architectures"):
            if len(architectures) != 1:
                raise ValidationException(
                    f"1 validation error detected: Value '[{', '.join(architectures)}]' at 'architectures' failed to "
                    f"satisfy constraint: Member must have length less than or equal to 1",
                )
            if architectures[0] not in ARCHITECTURES:
                raise ValidationException(
                    f"1 validation error detected: Value '[{', '.join(architectures)}]' at 'architectures' failed to "
                    f"satisfy constraint: Member must satisfy constraint: [Member must satisfy enum value set: "
                    f"[x86_64, arm64], Member must not be null]",
                )

        if env_vars := request.get("Environment", {}).get("Variables"):
            self._verify_env_variables(env_vars)

        if layers := request.get("Layers", []):
            self._validate_layers(layers, region=context_region, account_id=context_account_id)

        if not api_utils.is_role_arn(request.get("Role")):
            raise ValidationException(
                f"1 validation error detected: Value '{request.get('Role')}'"
                + " at 'role' failed to satisfy constraint: Member must satisfy regular expression pattern: arn:(aws[a-zA-Z-]*)?:iam::\\d{12}:role/?[a-zA-Z_0-9+=,.@\\-_/]+"
            )
        if not self.lambda_service.can_assume_role(request.get("Role"), context.region):
            raise InvalidParameterValueException(
                "The role defined for the function cannot be assumed by Lambda.", Type="User"
            )
        package_type = request.get("PackageType", PackageType.Zip)
        runtime = request.get("Runtime")
        self._validate_runtime(package_type, runtime)

        request_function_name = request.get("FunctionName")

        function_name, *_ = api_utils.get_name_and_qualifier(
            function_arn_or_name=request_function_name,
            qualifier=None,
            context=context,
        )

        if runtime in DEPRECATED_RUNTIMES:
            LOG.warning(
                "The Lambda runtime %s} is deprecated. "
                "Please upgrade the runtime for the function %s: "
                "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html",
                runtime,
                function_name,
            )
        if snap_start := request.get("SnapStart"):
            self._validate_snapstart(snap_start, runtime)
        if publish_to := request.get("PublishTo"):
            self._validate_publish_to(publish_to)
        state = lambda_stores[context_account_id][context_region]

        with self.create_fn_lock:
            if function_name in state.functions:
                raise ResourceConflictException(f"Function already exist: {function_name}")
            fn = Function(function_name=function_name)
            arn = VersionIdentifier(
                function_name=function_name,
                qualifier="$LATEST",
                region=context_region,
                account=context_account_id,
            )
            # save function code to s3
            code = None
            image = None
            image_config = None
            runtime_version_config = RuntimeVersionConfig(
                # Limitation: the runtime id (presumably sha256 of image) is currently hardcoded
                # Potential implementation: provide (cached) sha256 hash of used Docker image
                RuntimeVersionArn=f"arn:{context.partition}:lambda:{context_region}::runtime:8eeff65f6809a3ce81507fe733fe09b835899b99481ba22fd75b5a7338290ec1"
            )
            request_code = request.get("Code") or {}
            if package_type == PackageType.Zip:
                # TODO verify if correct combination of code is set
                if zip_file := request_code.get("ZipFile"):
                    code = store_lambda_archive(
                        archive_file=zip_file,
                        function_name=function_name,
                        region_name=context_region,
                        account_id=context_account_id,
                    )
                elif s3_bucket := request_code.get("S3Bucket"):
                    s3_key = request_code["S3Key"]
                    s3_object_version = request_code.get("S3ObjectVersion")
                    code = store_s3_bucket_archive(
                        archive_bucket=s3_bucket,
                        archive_key=s3_key,
                        archive_version=s3_object_version,
                        function_name=function_name,
                        region_name=context_region,
                        account_id=context_account_id,
                    )
                else:
                    raise LambdaServiceException("A ZIP file or S3 bucket is required")
            elif package_type == PackageType.Image:
                image = request_code.get("ImageUri")
                if not image:
                    raise LambdaServiceException(
                        "An image is required when the package type is set to 'image'"
                    )
                image = create_image_code(image_uri=image)

                image_config_req = request.get("ImageConfig") or {}
                image_config = ImageConfig(
                    command=image_config_req.get("Command"),
                    entrypoint=image_config_req.get("EntryPoint"),
                    working_directory=image_config_req.get("WorkingDirectory"),
                )
                # Runtime management controls are not available when providing a custom image
                runtime_version_config = None

            capacity_provider_config = None
            memory_size = request.get("MemorySize", LAMBDA_DEFAULT_MEMORY_SIZE)
            if "CapacityProviderConfig" in request:
                capacity_provider_config = request["CapacityProviderConfig"]
                self._validate_capacity_provider_config(capacity_provider_config, context)
                self._validate_managed_instances_runtime(runtime)

                default_config = CapacityProviderConfig(
                    LambdaManagedInstancesCapacityProviderConfig=LambdaManagedInstancesCapacityProviderConfig(
                        ExecutionEnvironmentMemoryGiBPerVCpu=2.0,
                        PerExecutionEnvironmentMaxConcurrency=16,
                    )
                )
                capacity_provider_config = merge_recursive(default_config, capacity_provider_config)
                memory_size = 2048
                if (request.get("LoggingConfig") or {}).get("LogFormat") == LogFormat.Text:
                    raise InvalidParameterValueException(
                        'LogLevel is not supported when LogFormat is set to "Text". Remove LogLevel from your request or change the LogFormat to "JSON" and try again.',
                        Type="User",
                    )
            if "LoggingConfig" in request:
                logging_config = request["LoggingConfig"]
                LOG.warning(
                    "Advanced Lambda Logging Configuration is currently mocked "
                    "and will not impact the logging behavior. "
                    "Please create a feature request if needed."
                )

                # when switching to JSON, app and system level log is auto set to INFO
                if logging_config.get("LogFormat", None) == LogFormat.JSON:
                    logging_config = {
                        "ApplicationLogLevel": "INFO",
                        "SystemLogLevel": "INFO",
                        "LogGroup": f"/aws/lambda/{function_name}",
                    } | logging_config
                else:
                    logging_config = (
                        LoggingConfig(
                            LogFormat=LogFormat.Text, LogGroup=f"/aws/lambda/{function_name}"
                        )
                        | logging_config
                    )

            elif capacity_provider_config:
                logging_config = LoggingConfig(
                    LogFormat=LogFormat.JSON,
                    LogGroup=f"/aws/lambda/{function_name}",
                    ApplicationLogLevel="INFO",
                    SystemLogLevel="INFO",
                )
            else:
                logging_config = LoggingConfig(
                    LogFormat=LogFormat.Text, LogGroup=f"/aws/lambda/{function_name}"
                )
            snap_start = (
                None
                if capacity_provider_config
                else SnapStartResponse(
                    ApplyOn=request.get("SnapStart", {}).get("ApplyOn", SnapStartApplyOn.None_),
                    OptimizationStatus=SnapStartOptimizationStatus.Off,
                )
            )
            version = FunctionVersion(
                id=arn,
                config=VersionFunctionConfiguration(
                    last_modified=api_utils.format_lambda_date(datetime.datetime.now()),
                    description=request.get("Description", ""),
                    role=request["Role"],
                    timeout=request.get("Timeout", LAMBDA_DEFAULT_TIMEOUT),
                    runtime=request.get("Runtime"),
                    memory_size=memory_size,
                    handler=request.get("Handler"),
                    package_type=package_type,
                    environment=env_vars,
                    architectures=request.get("Architectures") or [Architecture.x86_64],
                    tracing_config_mode=request.get("TracingConfig", {}).get(
                        "Mode", TracingMode.PassThrough
                    ),
                    image=image,
                    image_config=image_config,
                    code=code,
                    layers=self.map_layers(layers),
                    internal_revision=short_uid(),
                    ephemeral_storage=LambdaEphemeralStorage(
                        size=request.get("EphemeralStorage", {}).get("Size", 512)
                    ),
                    snap_start=snap_start,
                    runtime_version_config=runtime_version_config,
                    dead_letter_arn=request.get("DeadLetterConfig", {}).get("TargetArn"),
                    vpc_config=self._build_vpc_config(
                        context_account_id, context_region, request.get("VpcConfig")
                    ),
                    state=VersionState(
                        state=State.Pending,
                        code=StateReasonCode.Creating,
                        reason="The function is being created.",
                    ),
                    logging_config=logging_config,
                    # TODO: might need something like **optional_kwargs if None
                    #   -> Test with regular GetFunction (i.e., without a capacity provider)
                    capacity_provider_config=capacity_provider_config,
                ),
            )
            version_post_response = None
            if capacity_provider_config:
                version_post_response = dataclasses.replace(
                    version,
                    config=dataclasses.replace(
                        version.config,
                        last_update=UpdateStatus(status=LastUpdateStatus.Successful),
                        state=VersionState(state=State.ActiveNonInvocable),
                    ),
                )
            fn.versions["$LATEST"] = version_post_response or version
            state.functions[function_name] = fn
        initialization_type = (
            FunctionInitializationType.lambda_managed_instances
            if capacity_provider_config
            else FunctionInitializationType.on_demand
        )
        function_counter.labels(
            operation=FunctionOperation.create,
            runtime=runtime or "n/a",
            status=FunctionStatus.success,
            invocation_type="n/a",
            package_type=package_type,
            initialization_type=initialization_type,
        )
        # TODO: consider potential other side effects of not having a function version for $LATEST
        # Provisioning happens upon publishing for functions using a capacity provider
        if not capacity_provider_config:
            self.lambda_service.create_function_version(version)

        if tags := request.get("Tags"):
            # This will check whether the function exists.
            self._store_tags(arn.unqualified_arn(), tags)

        if request.get("Publish"):
            version = self._publish_version_with_changes(
                function_name=function_name,
                region=context_region,
                account_id=context_account_id,
                publish_to=request.get("PublishTo"),
            )

        if config.LAMBDA_SYNCHRONOUS_CREATE:
            # block via retrying until "terminal" condition reached before returning
            if not poll_condition(
                lambda: (
                    get_function_version(
                        function_name, version.id.qualifier, version.id.account, version.id.region
                    ).config.state.state
                    in [State.Active, State.ActiveNonInvocable, State.Failed]
                ),
                timeout=10,
            ):
                LOG.warning(
                    "LAMBDA_SYNCHRONOUS_CREATE is active, but waiting for %s reached timeout.",
                    function_name,
                )

        return api_utils.map_config_out(
            version, return_qualified_arn=False, return_update_status=False
        )