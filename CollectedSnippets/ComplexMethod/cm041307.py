def _build_run_create_cmd(
        self,
        action: str,
        image_name: str,
        *,
        name: str | None = None,
        entrypoint: list[str] | str | None = None,
        remove: bool = False,
        interactive: bool = False,
        tty: bool = False,
        detach: bool = False,
        command: list[str] | str | None = None,
        volumes: list[VolumeMappingSpecification] | None = None,
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
    ) -> tuple[list[str], str]:
        env_file = None
        cmd = self._docker_cmd() + [action]
        if remove:
            cmd.append("--rm")
        if name:
            cmd += ["--name", name]
        if entrypoint is not None:  # empty string entrypoint can be intentional
            if isinstance(entrypoint, str):
                cmd += ["--entrypoint", entrypoint]
            else:
                cmd += ["--entrypoint", shlex.join(entrypoint)]
        if privileged:
            cmd += ["--privileged"]
        if volumes:
            cmd += [
                param for volume in volumes for param in ["-v", self._map_to_volume_param(volume)]
            ]
        if interactive:
            cmd.append("--interactive")
        if tty:
            cmd.append("--tty")
        if detach:
            cmd.append("--detach")
        if ports:
            cmd += ports.to_list()
        if exposed_ports:
            cmd += list(itertools.chain.from_iterable(["--expose", port] for port in exposed_ports))
        if env_vars:
            env_flags, env_file = Util.create_env_vars_file_flag(env_vars)
            cmd += env_flags
        if user:
            cmd += ["--user", user]
        if cap_add:
            cmd += list(itertools.chain.from_iterable(["--cap-add", cap] for cap in cap_add))
        if cap_drop:
            cmd += list(itertools.chain.from_iterable(["--cap-drop", cap] for cap in cap_drop))
        if security_opt:
            cmd += list(
                itertools.chain.from_iterable(["--security-opt", opt] for opt in security_opt)
            )
        if network:
            cmd += ["--network", network]
        if dns:
            for dns_server in ensure_list(dns):
                cmd += ["--dns", dns_server]
        if workdir:
            cmd += ["--workdir", workdir]
        if labels:
            for key, value in labels.items():
                cmd += ["--label", f"{key}={value}"]
        if platform:
            cmd += ["--platform", platform]
        if ulimits:
            cmd += list(
                itertools.chain.from_iterable(["--ulimit", str(ulimit)] for ulimit in ulimits)
            )
        if init:
            cmd += ["--init"]
        if log_config:
            cmd += ["--log-driver", log_config.type]
            for key, value in log_config.config.items():
                cmd += ["--log-opt", f"{key}={value}"]
        if cpu_shares:
            cmd += ["--cpu-shares", str(cpu_shares)]
        if mem_limit:
            cmd += ["--memory", str(mem_limit)]

        if additional_flags:
            cmd += shlex.split(additional_flags)
        cmd.append(image_name)
        if command:
            cmd += command if isinstance(command, list) else [command]
        return cmd, env_file