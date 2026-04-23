def register(self, args: EnvironmentConfig) -> SupportContainer:
        """Record the container's runtime details. Must be used after the container has been started."""
        if self.details:
            raise Exception('Container already registered: %s' % self.name)

        try:
            container = docker_inspect(args, self.name)
        except ContainerNotFoundError:
            if not args.explain:
                raise

            # provide enough mock data to keep --explain working
            container = DockerInspect(args, dict(
                Id=self.container_id,
                NetworkSettings=dict(
                    IPAddress='127.0.0.1',
                    Ports=dict(('%d/tcp' % port, [dict(HostPort=random.randint(30000, 40000) if self.publish_ports else port)]) for port in self.ports),
                ),
                Config=dict(
                    Env=['%s=%s' % (key, value) for key, value in self.env.items()] if self.env else [],
                ),
            ))

        support_container_ip = get_container_ip_address(args, container)

        if self.publish_ports:
            # inspect the support container to locate the published ports
            tcp_ports = dict((port, container.get_tcp_port(port)) for port in self.ports)

            if any(not config or len(set(conf['HostPort'] for conf in config)) != 1 for config in tcp_ports.values()):
                raise ApplicationError('Unexpected `docker inspect` results for published TCP ports:\n%s' % json.dumps(tcp_ports, indent=4, sort_keys=True))

            published_ports = dict((port, int(config[0]['HostPort'])) for port, config in tcp_ports.items())
        else:
            published_ports = {}

        self.details = SupportContainer(
            container,
            support_container_ip,
            published_ports,
        )

        return self.details