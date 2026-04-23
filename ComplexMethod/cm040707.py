def update_function_configuration(
        self, context: RequestContext, request: UpdateFunctionConfigurationRequest
    ) -> FunctionConfiguration:
        """updates the $LATEST version of the function"""
        function_name = request.get("FunctionName")

        # in case we got ARN or partial ARN
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(function_name, None, context)
        state = lambda_stores[account_id][region]

        if function_name not in state.functions:
            raise ResourceNotFoundException(
                f"Function not found: {api_utils.unqualified_lambda_arn(function_name=function_name, region=region, account=account_id)}",
                Type="User",
            )
        function = state.functions[function_name]

        # TODO: lock modification of latest version
        # TODO: notify service for changes relevant to re-provisioning of $LATEST
        latest_version = function.latest()
        latest_version_config = latest_version.config

        revision_id = request.get("RevisionId")
        if revision_id and revision_id != latest_version.config.revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetFunction/GetAlias API to retrieve the latest Revision Id",
                Type="User",
            )

        replace_kwargs = {}
        if "EphemeralStorage" in request:
            replace_kwargs["ephemeral_storage"] = LambdaEphemeralStorage(
                request.get("EphemeralStorage", {}).get("Size", 512)
            )  # TODO: do defaults here apply as well?

        if "Role" in request:
            if not api_utils.is_role_arn(request["Role"]):
                raise ValidationException(
                    f"1 validation error detected: Value '{request.get('Role')}'"
                    + " at 'role' failed to satisfy constraint: Member must satisfy regular expression pattern: arn:(aws[a-zA-Z-]*)?:iam::\\d{12}:role/?[a-zA-Z_0-9+=,.@\\-_/]+"
                )
            replace_kwargs["role"] = request["Role"]

        if "Description" in request:
            replace_kwargs["description"] = request["Description"]

        if "Timeout" in request:
            replace_kwargs["timeout"] = request["Timeout"]

        if "MemorySize" in request:
            replace_kwargs["memory_size"] = request["MemorySize"]

        if "DeadLetterConfig" in request:
            replace_kwargs["dead_letter_arn"] = request.get("DeadLetterConfig", {}).get("TargetArn")

        if vpc_config := request.get("VpcConfig"):
            replace_kwargs["vpc_config"] = self._build_vpc_config(account_id, region, vpc_config)

        if "Handler" in request:
            replace_kwargs["handler"] = request["Handler"]

        if "Runtime" in request:
            runtime = request["Runtime"]

            if runtime not in ALL_RUNTIMES:
                raise InvalidParameterValueException(
                    f"Value {runtime} at 'runtime' failed to satisfy constraint: Member must satisfy enum value set: {VALID_RUNTIMES} or be a valid ARN",
                    Type="User",
                )
            if runtime in DEPRECATED_RUNTIMES:
                LOG.warning(
                    "The Lambda runtime %s is deprecated. "
                    "Please upgrade the runtime for the function %s: "
                    "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html",
                    runtime,
                    function_name,
                )
            replace_kwargs["runtime"] = request["Runtime"]

        if snap_start := request.get("SnapStart"):
            runtime = replace_kwargs.get("runtime") or latest_version_config.runtime
            self._validate_snapstart(snap_start, runtime)
            replace_kwargs["snap_start"] = SnapStartResponse(
                ApplyOn=snap_start.get("ApplyOn", SnapStartApplyOn.None_),
                OptimizationStatus=SnapStartOptimizationStatus.Off,
            )

        if "Environment" in request:
            if env_vars := request.get("Environment", {}).get("Variables", {}):
                self._verify_env_variables(env_vars)
            replace_kwargs["environment"] = env_vars

        if "Layers" in request:
            new_layers = request["Layers"]
            if new_layers:
                self._validate_layers(new_layers, region=region, account_id=account_id)
            replace_kwargs["layers"] = self.map_layers(new_layers)

        if "ImageConfig" in request:
            new_image_config = request["ImageConfig"]
            replace_kwargs["image_config"] = ImageConfig(
                command=new_image_config.get("Command"),
                entrypoint=new_image_config.get("EntryPoint"),
                working_directory=new_image_config.get("WorkingDirectory"),
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
                } | logging_config

            last_config = latest_version_config.logging_config

            # add partial update
            new_logging_config = last_config | logging_config

            # in case we switched from JSON to Text we need to remove LogLevel keys
            if (
                new_logging_config.get("LogFormat") == LogFormat.Text
                and last_config.get("LogFormat") == LogFormat.JSON
            ):
                new_logging_config.pop("ApplicationLogLevel", None)
                new_logging_config.pop("SystemLogLevel", None)

            replace_kwargs["logging_config"] = new_logging_config

        if "TracingConfig" in request:
            new_mode = request.get("TracingConfig", {}).get("Mode")
            if new_mode:
                replace_kwargs["tracing_config_mode"] = new_mode

        if "CapacityProviderConfig" in request:
            capacity_provider_config = request["CapacityProviderConfig"]
            self._validate_capacity_provider_config(capacity_provider_config, context)

            if latest_version.config.capacity_provider_config and not request[
                "CapacityProviderConfig"
            ].get("LambdaManagedInstancesCapacityProviderConfig"):
                raise ValidationException(
                    "1 validation error detected: Value null at 'capacityProviderConfig.lambdaManagedInstancesCapacityProviderConfig' failed to satisfy constraint: Member must not be null"
                )
            if not latest_version.config.capacity_provider_config:
                raise InvalidParameterValueException(
                    "CapacityProviderConfig isn't supported for Lambda Default functions.",
                    Type="User",
                )

            default_config = CapacityProviderConfig(
                LambdaManagedInstancesCapacityProviderConfig=LambdaManagedInstancesCapacityProviderConfig(
                    ExecutionEnvironmentMemoryGiBPerVCpu=2.0,
                    PerExecutionEnvironmentMaxConcurrency=16,
                )
            )
            capacity_provider_config = merge_recursive(default_config, capacity_provider_config)
            replace_kwargs["capacity_provider_config"] = capacity_provider_config
        new_latest_version = dataclasses.replace(
            latest_version,
            config=dataclasses.replace(
                latest_version_config,
                last_modified=api_utils.generate_lambda_date(),
                internal_revision=short_uid(),
                last_update=UpdateStatus(
                    status=LastUpdateStatus.InProgress,
                    code="Creating",
                    reason="The function is being created.",
                ),
                **replace_kwargs,
            ),
        )
        function.versions["$LATEST"] = new_latest_version  # TODO: notify

        if function.latest().config.capacity_provider_config:

            def _update_version_with_logging():
                try:
                    self.lambda_service.update_version(new_latest_version)
                except Exception:
                    LOG.error(
                        "Failed to update Lambda Managed Instances function version %s",
                        new_latest_version.id.qualified_arn(),
                        exc_info=LOG.isEnabledFor(logging.DEBUG),
                    )

            self.lambda_service.task_executor.submit(_update_version_with_logging)
        else:
            self.lambda_service.update_version(new_version=new_latest_version)

        return api_utils.map_config_out(new_latest_version)