def get_podman_init_config(self) -> InitConfig:
        """Return init config for running under Podman."""
        options = self.get_common_run_options()
        command: t.Optional[str] = None
        command_privileged = False
        expected_mounts: tuple[CGroupMount, ...]

        cgroup_version = get_docker_info(self.args).cgroup_version

        # Podman 4.4.0 updated containers/common to 0.51.0, which removed the SYS_CHROOT capability from the default list.
        # This capability is needed by services such as sshd, so is unconditionally added here.
        # See: https://github.com/containers/podman/releases/tag/v4.4.0
        # See: https://github.com/containers/common/releases/tag/v0.51.0
        # See: https://github.com/containers/common/pull/1240
        options.extend(('--cap-add', 'SYS_CHROOT'))

        # Without AUDIT_WRITE the following errors may appear in the system logs of a container after attempting to log in using SSH:
        #
        #   fatal: linux_audit_write_entry failed: Operation not permitted
        #
        # This occurs when running containers as root when the container host provides audit support, but the user lacks the AUDIT_WRITE capability.
        # The AUDIT_WRITE capability is provided by docker by default, but not podman.
        # See: https://github.com/moby/moby/pull/7179
        #
        # OpenSSH Portable requires AUDIT_WRITE when logging in with a TTY if the Linux audit feature was compiled in.
        # Containers with the feature enabled will require the AUDIT_WRITE capability when EPERM is returned while accessing the audit system.
        # See: https://github.com/openssh/openssh-portable/blob/2dc328023f60212cd29504fc05d849133ae47355/audit-linux.c#L90
        # See: https://github.com/openssh/openssh-portable/blob/715c892f0a5295b391ae92c26ef4d6a86ea96e8e/loginrec.c#L476-L478
        #
        # Some containers will be running a patched version of OpenSSH which blocks logins when EPERM is received while using the audit system.
        # These containers will require the AUDIT_WRITE capability when EPERM is returned while accessing the audit system.
        # See: https://src.fedoraproject.org/rpms/openssh/blob/f36/f/openssh-7.6p1-audit.patch
        #
        # Since only some containers carry the patch or enable the Linux audit feature in OpenSSH, this capability is enabled on a per-container basis.
        # No warning is provided when adding this capability, since there's not really anything the user can do about it.
        if self.config.audit == AuditMode.REQUIRED and detect_host_properties(self.args).audit_code == 'EPERM':
            options.extend(('--cap-add', 'AUDIT_WRITE'))

        # Without AUDIT_CONTROL the following errors may appear in the system logs of a container after attempting to log in using SSH:
        #
        #   pam_loginuid(sshd:session): Error writing /proc/self/loginuid: Operation not permitted
        #   pam_loginuid(sshd:session): set_loginuid failed
        #
        # Containers configured to use the pam_loginuid module will encounter this error. If the module is required, logins will fail.
        # Since most containers will have this configuration, the code to handle this issue is applied to all containers.
        #
        # This occurs when the loginuid is set on the container host and doesn't match the user on the container host which is running the container.
        # Container hosts which do not use systemd are likely to leave the loginuid unset and thus be unaffected.
        # The most common source of a mismatch is the use of sudo to run ansible-test, which changes the uid but cannot change the loginuid.
        # This condition typically occurs only under podman, since the loginuid is inherited from the current user.
        # See: https://github.com/containers/podman/issues/13012#issuecomment-1034049725
        #
        # This condition is detected by querying the loginuid of a container running on the container host.
        # When it occurs, a warning is displayed and the AUDIT_CONTROL capability is added to containers to work around the issue.
        # The warning serves as notice to the user that their usage of ansible-test is responsible for the additional capability requirement.
        if (loginuid := detect_host_properties(self.args).loginuid) not in (0, LOGINUID_NOT_SET, None):
            display.warning(f'Running containers with capability AUDIT_CONTROL since the container loginuid ({loginuid}) is incorrect. '
                            'This is most likely due to use of sudo to run ansible-test when loginuid is already set.', unique=True)

            options.extend(('--cap-add', 'AUDIT_CONTROL'))

        if self.config.cgroup == CGroupVersion.NONE:
            # Containers which do not require cgroup do not use systemd.

            options.extend((
                # Disabling systemd support in Podman will allow these containers to work on hosts without systemd.
                # Without this, running a container on a host without systemd results in errors such as (from crun):
                #   Error: crun: error stat'ing file `/sys/fs/cgroup/systemd`: No such file or directory:
                # A similar error occurs when using runc:
                #   OCI runtime attempted to invoke a command that was not found
                '--systemd', 'false',
                # A private cgroup namespace limits what is visible in /proc/*/cgroup.
                '--cgroupns', 'private',
                # Mounting a tmpfs overrides the cgroup mount(s) that would otherwise be provided by Podman.
                # This helps provide a consistent container environment across various container host configurations.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V1_ONLY) and cgroup_version == 1:
            # Podman hosts providing cgroup v1 will automatically bind mount the systemd hierarchy read-write in the container.
            # They will also create a dedicated cgroup v1 systemd hierarchy for the container.
            # On hosts with systemd this path is: /sys/fs/cgroup/systemd/libpod_parent/libpod-{container_id}/
            # On hosts without systemd this path is: /sys/fs/cgroup/systemd/{container_id}/

            options.extend((
                # Force Podman to enable systemd support since a command may be used later (to support pre-init diagnostics).
                '--systemd', 'always',
                # The host namespace must be used to permit the container to access the cgroup v1 systemd hierarchy created by Podman.
                '--cgroupns', 'host',
                # Mask the host cgroup tmpfs mount to avoid exposing the host cgroup v1 hierarchies (or cgroup v2 hybrid) to the container.
                # Podman will provide a cgroup v1 systemd hierarchy on top of this.
                '--tmpfs', '/sys/fs/cgroup',
            ))

            self.check_systemd_cgroup_v1(options)  # podman

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.TMPFS, writable=True, state=None),
                # The mount point can be writable or not.
                # The reason for the variation is not known.
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=None, state=CGroupState.HOST),
                # The filesystem type can be tmpfs or devtmpfs.
                # The reason for the variation is not known.
                CGroupMount(path=CGroupPath.SYSTEMD_RELEASE_AGENT, type=None, writable=False, state=None),
            )
        elif self.config.cgroup in (CGroupVersion.V1_V2, CGroupVersion.V2_ONLY) and cgroup_version == 2:
            # Podman hosts providing cgroup v2 will give each container a read-write cgroup mount.

            options.extend((
                # Force Podman to enable systemd support since a command may be used later (to support pre-init diagnostics).
                '--systemd', 'always',
                # A private cgroup namespace is used to avoid exposing the host cgroup to the container.
                '--cgroupns', 'private',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
            )
        elif self.config.cgroup == CGroupVersion.V1_ONLY and cgroup_version == 2:
            # Containers which require cgroup v1 need explicit volume mounts on container hosts not providing that version.
            # We must put the container PID 1 into the cgroup v1 systemd hierarchy we create.
            cgroup_path = self.create_systemd_cgroup_v1()  # podman
            command = f'echo 1 > {cgroup_path}/cgroup.procs'

            options.extend((
                # Force Podman to enable systemd support since a command is being provided.
                '--systemd', 'always',
                # A private cgroup namespace is required. Using the host cgroup namespace results in errors such as the following (from crun):
                #   Error: OCI runtime error: mount `/sys/fs/cgroup` to '/sys/fs/cgroup': Invalid argument
                # A similar error occurs when using runc:
                #   Error: OCI runtime error: runc create failed: unable to start container process: error during container init:
                #   error mounting "/sys/fs/cgroup" to rootfs at "/sys/fs/cgroup": mount /sys/fs/cgroup:/sys/fs/cgroup (via /proc/self/fd/7), flags: 0x1000:
                #   invalid argument
                '--cgroupns', 'private',
                # Unlike Docker, Podman ignores a /sys/fs/cgroup tmpfs mount, instead exposing a cgroup v2 mount.
                # The exposed volume will be read-write, but the container will have its own private namespace.
                # Provide a read-only cgroup v1 systemd hierarchy under which the dedicated ansible-test cgroup will be mounted read-write.
                # Without this systemd will fail while attempting to mount the cgroup v1 systemd hierarchy.
                # Podman doesn't support using a tmpfs for this. Attempting to do so results in an error (from crun):
                #   Error: OCI runtime error: read: Invalid argument
                # A similar error occurs when using runc:
                #   Error: OCI runtime error: runc create failed: unable to start container process: error during container init:
                #   error mounting "tmpfs" to rootfs at "/sys/fs/cgroup/systemd": tmpcopyup: failed to copy /sys/fs/cgroup/systemd to /proc/self/fd/7
                #   (/tmp/runctop3876247619/runctmpdir1460907418): read /proc/self/fd/7/cgroup.kill: invalid argument
                '--volume', '/sys/fs/cgroup/systemd:/sys/fs/cgroup/systemd:ro',
                # Provide the container access to the cgroup v1 systemd hierarchy created by ansible-test.
                '--volume', f'{cgroup_path}:{cgroup_path}:rw',
            ))

            expected_mounts = (
                CGroupMount(path=CGroupPath.ROOT, type=MountType.CGROUP_V2, writable=True, state=CGroupState.PRIVATE),
                CGroupMount(path=CGroupPath.SYSTEMD, type=MountType.CGROUP_V1, writable=False, state=CGroupState.SHADOWED),
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