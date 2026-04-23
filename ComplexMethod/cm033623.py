def provision(self) -> None:
        """Provision the host before delegation."""
        init_probe = self.args.dev_probe_cgroups is not None
        init_config = self.get_init_config()

        container = run_support_container(
            args=self.args,
            context='__test_hosts__',
            image=self.config.image,
            name=f'ansible-test-{self.label}',
            ports=[22],
            publish_ports=self.debugging_enabled or not self.controller,  # SSH to the controller is not required unless remote debugging is enabled
            options=init_config.options,
            cleanup=False,
            cmd=self.build_init_command(init_config, init_probe),
        )

        if not container:
            if self.args.prime_containers:
                if init_config.command_privileged or init_probe:
                    docker_pull(self.args, UTILITY_IMAGE)

            return

        self.container_name = container.name

        try:
            options = ['--pid', 'host', '--privileged']

            if init_config.command and init_config.command_privileged:
                init_command = init_config.command

                if not init_probe:
                    init_command += f' && {shlex.join(self.wake_command)}'

                cmd = ['nsenter', '-t', str(container.details.container.pid), '-m', '-p', 'sh', '-c', init_command]
                run_utility_container(self.args, f'ansible-test-init-{self.label}', cmd, options)

            if init_probe:
                check_container_cgroup_status(self.args, self.config, self.container_name, init_config.expected_mounts)

                cmd = ['nsenter', '-t', str(container.details.container.pid), '-m', '-p'] + self.wake_command
                run_utility_container(self.args, f'ansible-test-wake-{self.label}', cmd, options)
        except SubprocessError:
            display.info(f'Checking container "{self.container_name}" logs...')
            docker_logs(self.args, self.container_name)

            raise