def get_test_scenarios() -> list[TestScenario]:
    """Generate and return a list of test scenarios."""

    supported_engines = ('docker', 'podman')
    available_engines = [engine for engine in supported_engines if shutil.which(engine)]

    if not available_engines:
        raise ApplicationError(f'No supported container engines found: {", ".join(supported_engines)}')

    entries = get_container_completion_entries()

    unprivileged_user = User.get(UNPRIVILEGED_USER_NAME)

    scenarios: list[TestScenario] = []

    for container_name, settings in entries.items():
        image = settings['image']
        cgroup = settings.get('cgroup', 'v1-v2')

        if container_name == 'centos6' and os_release.id == 'alpine':
            # Alpine kernels do not emulate vsyscall by default, which causes the centos6 container to fail during init.
            # See: https://unix.stackexchange.com/questions/478387/running-a-centos-docker-image-on-arch-linux-exits-with-code-139
            # Other distributions enable settings which trap vsyscall by default.
            # See: https://www.kernelconfig.io/config_legacy_vsyscall_xonly
            # See: https://www.kernelconfig.io/config_legacy_vsyscall_emulate
            continue

        for engine in available_engines:
            # TODO: figure out how to get tests passing using docker without disabling selinux
            disable_selinux = os_release.id == 'fedora' and engine == 'docker' and cgroup != 'none'
            debug_systemd = cgroup != 'none'

            # The sleep+pkill used to support the cgroup probe causes problems with the centos6 container.
            # It results in sshd connections being refused or reset for many, but not all, container instances.
            # The underlying cause of this issue is unknown.
            probe_cgroups = container_name != 'centos6'

            # The default RHEL 9 crypto policy prevents use of SHA-1.
            # This results in SSH errors with centos6 containers: ssh_dispatch_run_fatal: Connection to 1.2.3.4 port 22: error in libcrypto
            # See: https://access.redhat.com/solutions/6816771
            enable_sha1 = os_release.id == 'rhel' and os_release.version_id.startswith('9.') and container_name == 'centos6'

            # Starting with Fedora 40, use of /usr/sbin/unix-chkpwd fails under Ubuntu 24.04 due to AppArmor.
            # This prevents SSH logins from completing due to unix-chkpwd failing to look up the user with getpwnam.
            # Disabling the 'unix-chkpwd' profile works around the issue, but does not solve the underlying problem.
            disable_apparmor_profile_unix_chkpwd = engine == 'podman' and os_release.id == 'ubuntu' and container_name.startswith('fedora')

            cgroup_version = get_docker_info(engine).cgroup_version

            user_scenarios = [
                # TODO: test rootless docker
                UserScenario(ssh=unprivileged_user),
            ]

            if engine == 'podman':
                if os_release.id not in ('ubuntu', 'fedora') \
                        and not (os_release.id == 'rhel' and os_release.version_id.startswith('10.')):
                    # rootfull podman is not supported by all systems
                    # rootfull podman networking stopped working on Fedora 43 hosts when docker is installed
                    # RHEL >= 10 is also excluded due to https://github.com/containers/crun/issues/2059
                    user_scenarios.append(UserScenario(ssh=ROOT_USER))

                # TODO: test podman remote on Alpine and Ubuntu hosts
                # TODO: combine remote with ssh using different unprivileged users
                if os_release.id not in ('alpine', 'ubuntu'):
                    user_scenarios.append(UserScenario(remote=unprivileged_user))

                if LOGINUID_MISMATCH and os_release.id not in ('ubuntu', 'fedora') \
                        and not (os_release.id == 'rhel' and os_release.version_id.startswith('10.')):
                    # rootfull podman is not supported by all systems
                    # rootfull podman networking stopped working on Fedora 43 hosts when docker is installed
                    # RHEL >= 10 is also excluded due to https://github.com/containers/crun/issues/2059
                    user_scenarios.append(UserScenario())

            for user_scenario in user_scenarios:
                expose_cgroup_version: int | None = None  # by default the host is assumed to provide sufficient cgroup support for the container and scenario

                if cgroup == 'v1-only' and cgroup_version != 1:
                    expose_cgroup_version = 1  # the container requires cgroup v1 support and the host does not use cgroup v1
                elif cgroup != 'none' and not have_systemd():
                    # the container requires cgroup support and the host does not use systemd
                    if cgroup_version == 1:
                        expose_cgroup_version = 1  # cgroup v1 mount required
                    elif cgroup_version == 2 and engine == 'podman' and user_scenario.actual != ROOT_USER:
                        # Running a systemd container on a non-systemd host with cgroup v2 fails for rootless podman.
                        # It may be possible to support this scenario, but the necessary configuration to do so is unknown.
                        display.warning(f'Skipping testing of {container_name!r} with rootless podman because the host uses cgroup v2 without systemd.')
                        continue

                scenarios.append(
                    TestScenario(
                        user_scenario=user_scenario,
                        engine=engine,
                        container_name=container_name,
                        image=image,
                        disable_selinux=disable_selinux,
                        expose_cgroup_version=expose_cgroup_version,
                        enable_sha1=enable_sha1,
                        debug_systemd=debug_systemd,
                        probe_cgroups=probe_cgroups,
                        disable_apparmor_profile_unix_chkpwd=disable_apparmor_profile_unix_chkpwd,
                    )
                )

    return scenarios