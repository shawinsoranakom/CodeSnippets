def check_cgroup_requirements(self) -> None:
        """Check cgroup requirements for the container."""
        cgroup_version = get_docker_info(self.args).cgroup_version

        if cgroup_version not in (1, 2):
            raise ApplicationError(f'The container host provides cgroup v{cgroup_version}, but only version v1 and v2 are supported.')

        # Stop early for containers which require cgroup v2 when the container host does not provide it.
        # None of the containers included with ansible-test currently use this configuration.
        # Support for v2-only was added in preparation for the eventual removal of cgroup v1 support from systemd after EOY 2023.
        # See: https://github.com/systemd/systemd/pull/24086
        if self.config.cgroup == CGroupVersion.V2_ONLY and cgroup_version != 2:
            raise ApplicationError(f'Container {self.config.name} requires cgroup v2 but the container host provides cgroup v{cgroup_version}.')

        # Containers which use old versions of systemd (earlier than version 226) require cgroup v1 support.
        # If the host is a cgroup v2 (unified) host, changes must be made to how the container is run.
        #
        # See: https://github.com/systemd/systemd/blob/main/NEWS
        #      Under the "CHANGES WITH 226" section:
        #      > systemd now optionally supports the new Linux kernel "unified" control group hierarchy.
        #
        # NOTE: The container host must have the cgroup v1 mount already present.
        #       If the container is run rootless, the user it runs under must have permissions to the mount.
        #
        # The following commands can be used to make the mount available:
        #
        #   mkdir /sys/fs/cgroup/systemd
        #   mount cgroup -t cgroup /sys/fs/cgroup/systemd -o none,name=systemd,xattr
        #   chown -R {user}:{group} /sys/fs/cgroup/systemd  # only when rootless
        #
        # See: https://github.com/containers/crun/blob/main/crun.1.md#runocisystemdforce_cgroup_v1path
        if self.config.cgroup == CGroupVersion.V1_ONLY or (self.config.cgroup != CGroupVersion.NONE and get_docker_info(self.args).cgroup_version == 1):
            if (cgroup_v1 := detect_host_properties(self.args).cgroup_v1) != SystemdControlGroupV1Status.VALID:
                if self.config.cgroup == CGroupVersion.V1_ONLY:
                    if get_docker_info(self.args).cgroup_version == 2:
                        reason = f'Container {self.config.name} requires cgroup v1, but the container host only provides cgroup v2.'
                    else:
                        reason = f'Container {self.config.name} requires cgroup v1, but the container host does not appear to be running systemd.'
                else:
                    reason = 'The container host provides cgroup v1, but does not appear to be running systemd.'

                reason += f'\n{cgroup_v1.value}'

                raise ControlGroupError(self.args, reason)