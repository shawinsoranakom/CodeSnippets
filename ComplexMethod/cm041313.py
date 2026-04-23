def create_container(
        self,
        image_name: str,
        *,
        name: str | None = None,
        entrypoint: list[str] | str | None = None,
        remove: bool = False,
        interactive: bool = False,
        tty: bool = False,
        detach: bool = False,
        command: list[str] | str | None = None,
        volumes: list[SimpleVolumeBind] | None = None,
        ports: PortMappings | None = None,
        exposed_ports: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
        user: str | None = None,
        cap_add: list[str] | None = None,
        cap_drop: list[str] | None = None,
        security_opt: list[str] | None = None,
        network: str | None = None,
        dns: str | list[str] | None = None,
        additional_flags: str | None = None,
        workdir: str | None = None,
        privileged: bool | None = None,
        labels: dict[str, str] | None = None,
        platform: DockerPlatform | None = None,
        ulimits: list[Ulimit] | None = None,
        init: bool | None = None,
        log_config: LogConfig | None = None,
        cpu_shares: int | None = None,
        mem_limit: int | str | None = None,
        auth_config: dict[str, str] | None = None,
    ) -> str:
        LOG.debug("Creating container with attributes: %s", locals())
        extra_hosts = None
        if additional_flags:
            parsed_flags = Util.parse_additional_flags(
                additional_flags,
                env_vars=env_vars,
                volumes=volumes,
                network=network,
                platform=platform,
                privileged=privileged,
                ports=ports,
                ulimits=ulimits,
                user=user,
                dns=dns,
            )
            env_vars = parsed_flags.env_vars
            extra_hosts = parsed_flags.extra_hosts
            volumes = parsed_flags.volumes
            labels = parsed_flags.labels
            network = parsed_flags.network
            platform = parsed_flags.platform
            privileged = parsed_flags.privileged
            ports = parsed_flags.ports
            ulimits = parsed_flags.ulimits
            user = parsed_flags.user
            dns = parsed_flags.dns

        try:
            kwargs = {}
            if cap_add:
                kwargs["cap_add"] = cap_add
            if cap_drop:
                kwargs["cap_drop"] = cap_drop
            if security_opt:
                kwargs["security_opt"] = security_opt
            if dns:
                kwargs["dns"] = ensure_list(dns)
            if exposed_ports:
                # This is not exactly identical to --expose, as they are listed in the "HostConfig" on docker inspect
                # but the behavior should be identical
                kwargs["ports"] = {port: [] for port in exposed_ports}
            if ports:
                kwargs.setdefault("ports", {})
                kwargs["ports"].update(ports.to_dict())
            if workdir:
                kwargs["working_dir"] = workdir
            if privileged:
                kwargs["privileged"] = True
            if init:
                kwargs["init"] = True
            if labels:
                kwargs["labels"] = labels
            if log_config:
                kwargs["log_config"] = DockerLogConfig(
                    type=log_config.type, config=log_config.config
                )
            if ulimits:
                kwargs["ulimits"] = [
                    docker.types.Ulimit(
                        name=ulimit.name, soft=ulimit.soft_limit, hard=ulimit.hard_limit
                    )
                    for ulimit in ulimits
                ]
            if cpu_shares:
                kwargs["cpu_shares"] = cpu_shares
            if mem_limit:
                kwargs["mem_limit"] = mem_limit
            mounts = None
            if volumes:
                mounts = Util.convert_mount_list_to_dict(volumes)

            image_name = self.registry_resolver_strategy.resolve(image_name)

            def create_container():
                return self.client().containers.create(
                    image=image_name,
                    command=command,
                    auto_remove=remove,
                    name=name,
                    stdin_open=interactive,
                    tty=tty,
                    entrypoint=entrypoint,
                    environment=env_vars,
                    detach=detach,
                    user=user,
                    network=network,
                    volumes=mounts,
                    extra_hosts=extra_hosts,
                    platform=platform,
                    **kwargs,
                )

            try:
                container = create_container()
            except ImageNotFound:
                LOG.debug("Image not found. Pulling image %s", image_name)
                self.pull_image(image_name, platform, auth_config=auth_config)
                container = create_container()
            return container.id
        except ImageNotFound:
            raise NoSuchImage(image_name)
        except APIError as e:
            raise ContainerException() from e