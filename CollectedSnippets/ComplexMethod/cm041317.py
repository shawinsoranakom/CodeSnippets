def parse_additional_flags(
        additional_flags: str,
        env_vars: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        volumes: list[SimpleVolumeBind] | None = None,
        network: str | None = None,
        platform: DockerPlatform | None = None,
        ports: PortMappings | None = None,
        privileged: bool | None = None,
        user: str | None = None,
        ulimits: list[Ulimit] | None = None,
        dns: str | list[str] | None = None,
    ) -> DockerRunFlags:
        """Parses additional CLI-formatted Docker flags, which could overwrite provided defaults.
        :param additional_flags: String which contains the flag definitions inspired by the Docker CLI reference:
                                 https://docs.docker.com/engine/reference/commandline/run/
        :param env_vars: Dict with env vars. Will be modified in place.
        :param labels: Dict with labels. Will be modified in place.
        :param volumes: List of mount tuples (host_path, container_path). Will be modified in place.
        :param network: Existing network name (optional). Warning will be printed if network is overwritten in flags.
        :param platform: Platform to execute container. Warning will be printed if platform is overwritten in flags.
        :param ports: PortMapping object. Will be modified in place.
        :param privileged: Run the container in privileged mode. Warning will be printed if overwritten in flags.
        :param ulimits: ulimit options in the format <type>=<soft limit>[:<hard limit>]
        :param user: User to run first process. Warning will be printed if user is overwritten in flags.
        :param dns: List of DNS servers to configure the container with.
        :return: A DockerRunFlags object that will return new objects if respective parameters were None and
                additional flags contained a flag for that object or the same which are passed otherwise.
        """
        # Argparse refactoring opportunity: custom argparse actions can be used to modularize parsing (e.g., key=value)
        # https://docs.python.org/3/library/argparse.html#action

        # Configure parser
        parser = NoExitArgumentParser(description="Docker run flags parser")
        parser.add_argument(
            "--add-host",
            help="Add a custom host-to-IP mapping (host:ip)",
            dest="add_hosts",
            action="append",
        )
        parser.add_argument(
            "--env", "-e", help="Set environment variables", dest="envs", action="append"
        )
        parser.add_argument(
            "--env-file",
            help="Set environment variables via a file",
            dest="env_files",
            action="append",
        )
        parser.add_argument(
            "--compose-env-file",
            help="Set environment variables via a file, with a docker-compose supported feature set.",
            dest="compose_env_files",
            action="append",
        )
        parser.add_argument(
            "--label", "-l", help="Add container meta data", dest="labels", action="append"
        )
        parser.add_argument("--network", help="Connect a container to a network")
        parser.add_argument(
            "--platform",
            type=DockerPlatform,
            help="Docker platform (e.g., linux/amd64 or linux/arm64)",
        )
        parser.add_argument(
            "--privileged",
            help="Give extended privileges to this container",
            action="store_true",
        )
        parser.add_argument(
            "--publish",
            "-p",
            help="Publish container port(s) to the host",
            dest="publish_ports",
            action="append",
        )
        parser.add_argument(
            "--ulimit", help="Container ulimit settings", dest="ulimits", action="append"
        )
        parser.add_argument("--user", "-u", help="Username or UID to execute first process")
        parser.add_argument(
            "--volume", "-v", help="Bind mount a volume", dest="volumes", action="append"
        )
        parser.add_argument("--dns", help="Set custom DNS servers", dest="dns", action="append")

        # Parse
        flags = shlex.split(additional_flags)
        args = parser.parse_args(flags)

        # Post-process parsed flags
        extra_hosts = None
        if args.add_hosts:
            for add_host in args.add_hosts:
                extra_hosts = extra_hosts if extra_hosts is not None else {}
                hosts_split = add_host.split(":")
                extra_hosts[hosts_split[0]] = hosts_split[1]

        # set env file values before env values, as the latter override the earlier
        if args.env_files:
            env_vars = env_vars if env_vars is not None else {}
            for env_file in args.env_files:
                env_vars.update(Util._read_docker_cli_env_file(env_file))

        if args.compose_env_files:
            env_vars = env_vars if env_vars is not None else {}
            for env_file in args.compose_env_files:
                env_vars.update(dotenv.dotenv_values(env_file))

        if args.envs:
            env_vars = env_vars if env_vars is not None else {}
            for env in args.envs:
                lhs, _, rhs = env.partition("=")
                env_vars[lhs] = rhs

        if args.labels:
            labels = labels if labels is not None else {}
            for label in args.labels:
                key, _, value = label.partition("=")
                # Only consider non-empty labels
                if key:
                    labels[key] = value

        if args.network:
            LOG.warning(
                "Overwriting Docker container network '%s' with new value '%s'",
                network,
                args.network,
            )
            network = args.network

        if args.platform:
            LOG.warning(
                "Overwriting Docker platform '%s' with new value '%s'",
                platform,
                args.platform,
            )
            platform = args.platform

        if args.privileged:
            LOG.warning(
                "Overwriting Docker container privileged flag %s with new value %s",
                privileged,
                args.privileged,
            )
            privileged = args.privileged

        if args.publish_ports:
            for port_mapping in args.publish_ports:
                port_split = port_mapping.split(":")
                protocol = "tcp"
                if len(port_split) == 2:
                    host_port, container_port = port_split
                elif len(port_split) == 3:
                    LOG.warning(
                        "Host part of port mappings are ignored currently in additional flags"
                    )
                    _, host_port, container_port = port_split
                else:
                    raise ValueError(f"Invalid port string provided: {port_mapping}")
                host_port_split = host_port.split("-")
                if len(host_port_split) == 2:
                    host_port = [int(host_port_split[0]), int(host_port_split[1])]
                elif len(host_port_split) == 1:
                    host_port = int(host_port)
                else:
                    raise ValueError(f"Invalid port string provided: {port_mapping}")
                if "/" in container_port:
                    container_port, protocol = container_port.split("/")
                ports = ports if ports is not None else PortMappings()
                ports.add(host_port, int(container_port), protocol)

        if args.ulimits:
            ulimits = ulimits if ulimits is not None else []
            ulimits_dict = {ul.name: ul for ul in ulimits}
            for ulimit in args.ulimits:
                name, _, rhs = ulimit.partition("=")
                soft, _, hard = rhs.partition(":")
                hard_limit = int(hard) if hard else int(soft)
                new_ulimit = Ulimit(name=name, soft_limit=int(soft), hard_limit=hard_limit)
                if ulimits_dict.get(name):
                    LOG.warning("Overwriting Docker ulimit %s", new_ulimit)
                ulimits_dict[name] = new_ulimit
            ulimits = list(ulimits_dict.values())

        if args.user:
            LOG.warning(
                "Overwriting Docker user '%s' with new value '%s'",
                user,
                args.user,
            )
            user = args.user

        if args.volumes:
            volumes = volumes if volumes is not None else []
            for volume in args.volumes:
                match = re.match(
                    r"(?P<host>[\w\s\\\/:\-.]+?):(?P<container>[\w\s\/\-.]+)(?::(?P<arg>ro|rw|z|Z))?",
                    volume,
                )
                if not match:
                    LOG.warning("Unable to parse volume mount Docker flags: %s", volume)
                    continue
                host_path = match.group("host")
                container_path = match.group("container")
                rw_args = match.group("arg")
                if rw_args:
                    LOG.info("Volume options like :ro or :rw are currently ignored.")
                volumes.append((host_path, container_path))

        dns = ensure_list(dns or [])
        if args.dns:
            LOG.info(
                "Extending Docker container DNS servers %s with additional values %s", dns, args.dns
            )
            dns.extend(args.dns)

        return DockerRunFlags(
            env_vars=env_vars,
            extra_hosts=extra_hosts,
            labels=labels,
            volumes=volumes,
            ports=ports,
            network=network,
            platform=platform,
            privileged=privileged,
            ulimits=ulimits,
            user=user,
            dns=dns,
        )