def start(self, env_vars: dict[str, str]) -> None:
        self.executor_endpoint.start()
        main_network, *additional_networks = self._get_networks_for_executor()
        container_config = LambdaContainerConfiguration(
            image_name=None,
            name=self.container_name,
            env_vars=env_vars,
            network=main_network,
            entrypoint=RAPID_ENTRYPOINT,
            platform=docker_platform(self.function_version.config.architectures[0]),
            additional_flags=config.LAMBDA_DOCKER_FLAGS,
        )

        if self.function_version.config.package_type == PackageType.Zip:
            if self.function_version.config.code.is_hot_reloading():
                container_config.env_vars[HOT_RELOADING_ENV_VARIABLE] = "/var/task"
                if container_config.volumes is None:
                    container_config.volumes = VolumeMappings()
                container_config.volumes.add(
                    BindMount(
                        str(self.function_version.config.code.get_unzipped_code_location()),
                        "/var/task",
                        read_only=True,
                    )
                )
            else:
                container_config.copy_folders.append(
                    (
                        f"{str(self.function_version.config.code.get_unzipped_code_location())}/.",
                        "/var/task",
                    )
                )

        # always chmod /tmp to 700
        chmod_paths = [ChmodPath(path="/tmp", mode="0700")]

        # set the dns server of the lambda container to the LocalStack container IP
        # the dns server will automatically respond with the right target for transparent endpoint injection
        if config.LAMBDA_DOCKER_DNS:
            # Don't overwrite DNS container config if it is already set (e.g., using LAMBDA_DOCKER_DNS)
            LOG.warning(
                "Container DNS overridden to %s, connection to names pointing to LocalStack, like 'localhost.localstack.cloud' will need additional configuration.",
                config.LAMBDA_DOCKER_DNS,
            )
            container_config.dns = config.LAMBDA_DOCKER_DNS
        else:
            if dns_server.is_server_running():
                # Set the container DNS to LocalStack to resolve localhost.localstack.cloud and
                # enable transparent endpoint injection (Pro image only).
                container_config.dns = self.get_endpoint_from_executor()

        lambda_hooks.start_docker_executor.run(container_config, self.function_version)

        if not container_config.image_name:
            container_config.image_name = self.get_image()
        if config.LAMBDA_DEV_PORT_EXPOSE:
            self.executor_endpoint.container_port = get_free_tcp_port()
            if container_config.ports is None:
                container_config.ports = PortMappings()
            container_config.ports.add(self.executor_endpoint.container_port, INVOCATION_PORT)

        if config.LAMBDA_INIT_DEBUG:
            container_config.entrypoint = "/debug-bootstrap.sh"
            if not container_config.ports:
                container_config.ports = PortMappings()
            container_config.ports.add(config.LAMBDA_INIT_DELVE_PORT, config.LAMBDA_INIT_DELVE_PORT)

        if (
            self.function_version.config.layers
            and not config.LAMBDA_PREBUILD_IMAGES
            and self.function_version.config.package_type == PackageType.Zip
        ):
            # avoid chmod on mounted code paths
            hot_reloading_env = container_config.env_vars.get(HOT_RELOADING_ENV_VARIABLE, "")
            if "/opt" not in hot_reloading_env:
                chmod_paths.append(ChmodPath(path="/opt", mode="0755"))
            if "/var/task" not in hot_reloading_env:
                chmod_paths.append(ChmodPath(path="/var/task", mode="0755"))
        container_config.env_vars["LOCALSTACK_CHMOD_PATHS"] = json.dumps(chmod_paths)

        CONTAINER_CLIENT.create_container_from_config(container_config)
        if (
            not config.LAMBDA_PREBUILD_IMAGES
            or self.function_version.config.package_type != PackageType.Zip
        ):
            CONTAINER_CLIENT.copy_into_container(
                self.container_name, f"{str(get_runtime_client_path())}/.", "/"
            )
            # tiny bit inefficient since we actually overwrite the init, but otherwise the path might not exist
            if config.LAMBDA_INIT_BIN_PATH:
                CONTAINER_CLIENT.copy_into_container(
                    self.container_name, config.LAMBDA_INIT_BIN_PATH, "/var/rapid/init"
                )
            if config.LAMBDA_INIT_DEBUG:
                CONTAINER_CLIENT.copy_into_container(
                    self.container_name, config.LAMBDA_INIT_DELVE_PATH, "/var/rapid/dlv"
                )
                CONTAINER_CLIENT.copy_into_container(
                    self.container_name, config.LAMBDA_INIT_BOOTSTRAP_PATH, "/debug-bootstrap.sh"
                )

        if not config.LAMBDA_PREBUILD_IMAGES:
            # copy_folders should be empty here if package type is not zip
            for source, target in container_config.copy_folders:
                CONTAINER_CLIENT.copy_into_container(self.container_name, source, target)

        if additional_networks:
            for additional_network in additional_networks:
                CONTAINER_CLIENT.connect_container_to_network(
                    additional_network, self.container_name
                )

        CONTAINER_CLIENT.start_container(self.container_name)
        # still using main network as main entrypoint
        self.ip = CONTAINER_CLIENT.get_container_ipv4_for_network(
            container_name_or_id=self.container_name, container_network=main_network
        )
        if config.LAMBDA_DEV_PORT_EXPOSE:
            self.ip = "127.0.0.1"
        self.executor_endpoint.container_address = self.ip

        self.executor_endpoint.wait_for_startup()