def get_docker_init_config(self) -> InitConfig:
        """Return init config for running under Docker."""
        options = self.get_common_run_options()
        command: t.Optional[str] = None
        command_privileged = False
        expected_mounts: tuple[CGroupMount, ...]

        docker_socket = '/var/run/docker.sock'

        if get_docker_hostname() != 'localhost' or os.path.exists(docker_socket):
            options.extend(['--volume', f'{docker_socket}:{docker_socket}'])

        cgroup_version = get_docker_info(self.args).cgroup_version

        if self.config.cgroup == CGroupVersion.NONE:
            # Containers which do not require cgroup do not use systemd.

            if get_docker_info(self.args).cgroupns_option_supported:
                # Use the `--cgroupns` option if it is supported.
                # Older servers which do not support the option use the host group namespace.
                # Older clients which do not support the option cause newer servers to use the host cgroup namespace (cgroup v1 only).
                # See: https://github.com/moby/moby/blob/master/api/server/router/container/container_routes.go#L512-L517
                # If the host cgroup namespace is used, cgroup information will be visible, but the cgroup mounts will be unavailable due to the tmpfs below.
                options.extend((
                    # A private cgroup namespace limits what is visible in /proc/*/cgroup.
                    '--cgroupns', 'private',
                ))

            options.extend((
                # Mounting a tmpfs overrides the cgroup mount(s) that would otherwise be provided by Docker.
                # This helps provide a consistent container environment across various container host configurations.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V1_ONLY) and cgroup_version == 1:
            # Docker hosts providing cgroup v1 will automatically bind mount the systemd hierarchy read-only in the container.
            # They will also create a dedicated cgroup v1 systemd hierarchy for the container.
            # The cgroup v1 system hierarchy path is: /sys/fs/cgroup/systemd/{container_id}/

            if get_docker_info(self.args).cgroupns_option_supported:
                # Use the `--cgroupns` option if it is supported.
                # Older servers which do not support the option use the host group namespace.
                # Older clients which do not support the option cause newer servers to use the host cgroup namespace (cgroup v1 only).
                # See: https://github.com/moby/moby/blob/master/api/server/router/container/container_routes.go#L512-L517
                options.extend((
                    # The host cgroup namespace must be used.
                    # Otherwise, /proc/1/cgroup will report "/" for the cgroup path, which is incorrect.
                    # See: https://github.com/systemd/systemd/issues/19245#issuecomment-815954506
                    # It is set here to avoid relying on the current Docker configuration.
                    '--cgroupns', 'host',
                ))

            options.extend((
                # Mask the host cgroup tmpfs mount to avoid exposing the host cgroup v1 hierarchies (or cgroup v2 hybrid) to the container.
                '--tmpfs', '/sys/fs/cgroup',
                # A cgroup v1 systemd hierarchy needs to be mounted read-write over the read-only one provided by Docker.
                # Alternatives were tested, but were unusable due to various issues:
                #  - Attempting to remount the existing mount point read-write will result in a "mount point is busy" error.
                #  - Adding the entire "/sys/fs/cgroup" mount will expose hierarchies other than systemd.
                #    If the host is a cgroup v2 hybrid host it would also expose the /sys/fs/cgroup/unified/ hierarchy read-write.
                #    On older systems, such as an Ubuntu 18.04 host, a dedicated v2 cgroup would not be used, exposing the host cgroups to the container.
                '--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:rw',
            ))

            self.check_systemd_cgroup_v1(options)  # docker

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=True, state=CGroupState.HOST),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V2_ONLY) and cgroup_version == 2:
            # Docker hosts providing cgroup v2 will give each container a read-only cgroup mount.
            # It must be remounted read-write before systemd starts.
            # This must be done in a privileged container, otherwise a "permission denied" error can occur.
            command = 'mount -o remount,rw /sys/fs/cgroup/'
            command_privileged = True

            options.extend((
                # A private cgroup namespace is used to avoid exposing the host cgroup to the container.
                # This matches the behavior in Podman 1.7.0 and later, which select cgroupns 'host' mode for cgroup v1 and 'private' mode for cgroup v2.
                # See: https://github.com/containers/podman/pull/4374
                # See: https://github.com/containers/podman/blob/main/RELEASE_NOTES.md#170
                '--cgroupns', 'private',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
            )
        elif self.config.cgroup == CGroupVersion.V1_ONLY and cgroup_version == 2:
            # Containers which require cgroup v1 need explicit volume mounts on container hosts not providing that version.
            # We must put the container PID 1 into the cgroup v1 systemd hierarchy we create.
            cgroup_path = self.create_systemd_cgroup_v1()  # docker
            command = f'echo 1 > {cgroup_path}/cgroup.procs'

            options.extend((
                # A private cgroup namespace is used since no access to the host cgroup namespace is required.
                # This matches the configuration used for running cgroup v1 containers under Podman.
                '--cgroupns', 'private',
                # Provide a read-write tmpfs filesystem to support additional cgroup mount points.
                # Without this Docker will provide a read-only cgroup2 mount instead.
                '--tmpfs', '/sys/fs/cgroup',
                # Provide a read-write tmpfs filesystem to simulate a systemd cgroup v1 hierarchy.
                # Without this systemd will fail while attempting to mount the cgroup v1 systemd hierarchy.
                '--tmpfs', '/sys/fs/cgroup/systemd',
                # Provide the container access to the cgroup v1 systemd hierarchy created by ansible-test.
                '--volume', f'{cgroup_path}:{cgroup_path}:rw',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.TMPFS, writable=True, state=None),
                CGroupMount(path=cgroup_path, type=MountType.CGROUP_V1, writable=True, state=CGroupState.HOST),
            )
        else:
            raise InternalError(f'Unhandled cgroup configuration: {self.config.cgroup} on cgroup v{cgroup_version}.')

        return self.InitConfig(
            options=options,
            command=command,
            command_privileged=command_privileged,
            expected_mounts=expected_mounts,
        )