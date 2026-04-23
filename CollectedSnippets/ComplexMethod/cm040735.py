def get_environment_variables(self) -> dict[str, str]:
        """
        Returns the environment variable set for the runtime container
        :return: Dict of environment variables
        """
        credentials = self.get_credentials()
        env_vars = {
            # 1) Public AWS defined runtime environment variables (in same order):
            # https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
            # a) Reserved environment variables
            # _HANDLER conditionally added below
            # TODO: _X_AMZN_TRACE_ID
            "AWS_DEFAULT_REGION": self.function_version.id.region,
            "AWS_REGION": self.function_version.id.region,
            # AWS_EXECUTION_ENV conditionally added below
            "AWS_LAMBDA_FUNCTION_NAME": self.function_version.id.function_name,
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": self.function_version.config.memory_size,
            "AWS_LAMBDA_FUNCTION_VERSION": self.function_version.id.qualifier,
            "AWS_LAMBDA_INITIALIZATION_TYPE": self.initialization_type,
            "AWS_LAMBDA_LOG_GROUP_NAME": self.get_log_group_name(),
            "AWS_LAMBDA_LOG_STREAM_NAME": self.get_log_stream_name(),
            # Access IDs for role
            "AWS_ACCESS_KEY_ID": credentials["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": credentials["SecretAccessKey"],
            "AWS_SESSION_TOKEN": credentials["SessionToken"],
            # AWS_LAMBDA_RUNTIME_API is set in the runtime interface emulator (RIE)
            "LAMBDA_TASK_ROOT": "/var/task",
            "LAMBDA_RUNTIME_DIR": "/var/runtime",
            # b) Unreserved environment variables
            # LANG
            # LD_LIBRARY_PATH
            # NODE_PATH
            # PYTHONPATH
            # GEM_PATH
            "AWS_XRAY_CONTEXT_MISSING": "LOG_ERROR",
            # TODO: allow configuration of xray address
            "AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1:2000",
            # not 100% sure who sets these two
            # extensions are not supposed to have them in their envs => TODO: test if init removes them
            "_AWS_XRAY_DAEMON_PORT": "2000",
            "_AWS_XRAY_DAEMON_ADDRESS": "127.0.0.1",
            # AWS_LAMBDA_DOTNET_PREJIT
            "TZ": ":UTC",
            # 2) Public AWS RIE interface: https://github.com/aws/aws-lambda-runtime-interface-emulator
            "AWS_LAMBDA_FUNCTION_TIMEOUT": self.function_version.config.timeout,
            # 3) Public LocalStack endpoint
            "LOCALSTACK_HOSTNAME": self.runtime_executor.get_endpoint_from_executor(),
            "EDGE_PORT": str(config.GATEWAY_LISTEN[0].port),
            # AWS_ENDPOINT_URL conditionally added below
            # 4) Internal LocalStack runtime API
            "LOCALSTACK_RUNTIME_ID": self.id,
            "LOCALSTACK_RUNTIME_ENDPOINT": self.runtime_executor.get_runtime_endpoint(),
            # 5) Account of the function (necessary for extensions API)
            "LOCALSTACK_FUNCTION_ACCOUNT_ID": self.function_version.id.account,
            # used by the init to spawn the x-ray daemon
            # LOCALSTACK_USER conditionally added below
        }
        # Conditionally added environment variables
        # Lambda advanced logging controls:
        # https://aws.amazon.com/blogs/compute/introducing-advanced-logging-controls-for-aws-lambda-functions/
        logging_config = self.function_version.config.logging_config
        if logging_config.get("LogFormat") == LogFormat.JSON:
            env_vars["AWS_LAMBDA_LOG_FORMAT"] = logging_config["LogFormat"]
            # TODO: test this (currently not implemented in LocalStack)
            env_vars["AWS_LAMBDA_LOG_LEVEL"] = logging_config["ApplicationLogLevel"].capitalize()
        # Lambda Managed Instances
        if capacity_provider_config := self.function_version.config.capacity_provider_config:
            # Disable dropping privileges for parity
            # TODO: implement mixed permissions (maybe in RIE)
            # env_vars["LOCALSTACK_USER"] = "root"
            env_vars["AWS_LAMBDA_MAX_CONCURRENCY"] = capacity_provider_config[
                "LambdaManagedInstancesCapacityProviderConfig"
            ]["PerExecutionEnvironmentMaxConcurrency"]
            env_vars["TZ"] = ":/etc/localtime"
        if not config.LAMBDA_DISABLE_AWS_ENDPOINT_URL:
            env_vars["AWS_ENDPOINT_URL"] = (
                f"http://{self.runtime_executor.get_endpoint_from_executor()}:{config.GATEWAY_LISTEN[0].port}"
            )
        # config.handler is None for image lambdas and will be populated at runtime (e.g., by RIE)
        if self.function_version.config.handler:
            env_vars["_HANDLER"] = self.function_version.config.handler
        # Will be overridden by the runtime itself unless it is a provided runtime
        if self.function_version.config.runtime:
            env_vars["AWS_EXECUTION_ENV"] = "AWS_Lambda_rapid"
        if config.LAMBDA_INIT_DEBUG:
            # Disable dropping privileges because it breaks debugging
            env_vars["LOCALSTACK_USER"] = "root"
        # Forcefully overwrite the user might break debugging!
        if config.LAMBDA_INIT_USER is not None:
            env_vars["LOCALSTACK_USER"] = config.LAMBDA_INIT_USER
        if config.LS_LOG in config.TRACE_LOG_LEVELS:
            env_vars["LOCALSTACK_INIT_LOG_LEVEL"] = "info"
        if config.LAMBDA_INIT_POST_INVOKE_WAIT_MS:
            env_vars["LOCALSTACK_POST_INVOKE_WAIT_MS"] = int(config.LAMBDA_INIT_POST_INVOKE_WAIT_MS)
        if config.LAMBDA_LIMITS_MAX_FUNCTION_PAYLOAD_SIZE_BYTES:
            env_vars["LOCALSTACK_MAX_PAYLOAD_SIZE"] = int(
                config.LAMBDA_LIMITS_MAX_FUNCTION_PAYLOAD_SIZE_BYTES
            )

        # Let users overwrite any environment variable at last (if they want so)
        if self.function_version.config.environment:
            env_vars.update(self.function_version.config.environment)
        return env_vars