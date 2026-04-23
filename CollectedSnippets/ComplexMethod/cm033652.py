def detect_host_properties(args: CommonConfig) -> ContainerHostProperties:
    """
    Detect and return properties of the container host.

    The information collected is:

      - The errno result from attempting to query the container host's audit status.
      - The max number of open files supported by the container host to run containers.
        This value may be capped to the maximum value used by ansible-test.
        If the value is below the desired limit, a warning is displayed.
      - The loginuid used by the container host to run containers, or None if the audit subsystem is unavailable.
      - The cgroup subsystems registered with the Linux kernel.
      - The mounts visible within a container.
      - The status of the systemd cgroup v1 hierarchy.

    This information is collected together to reduce the number of container runs to probe the container host.
    """
    try:
        return detect_host_properties.properties  # type: ignore[attr-defined]
    except AttributeError:
        pass

    single_line_commands = (
        'audit-status',
        'cat /proc/sys/fs/nr_open',
        'ulimit -Hn',
        '(cat /proc/1/loginuid; echo)',
    )

    multi_line_commands = (
        ' && '.join(single_line_commands),
        'cat /proc/1/cgroup',
        'cat /proc/1/mountinfo',
    )

    options = ['--volume', '/sys/fs/cgroup:/probe:ro']
    cmd = ['sh', '-c', ' && echo "-" && '.join(multi_line_commands)]

    stdout, stderr = run_utility_container(args, 'ansible-test-probe', cmd, options)

    if args.explain:
        return ContainerHostProperties(
            audit_code='???',
            max_open_files=MAX_NUM_OPEN_FILES,
            loginuid=LOGINUID_NOT_SET,
            cgroup_v1=SystemdControlGroupV1Status.VALID,
            cgroup_v2=False,
        )

    blocks = stdout.split('\n-\n')

    if len(blocks) != len(multi_line_commands):
        message = f'Unexpected probe output. Expected {len(multi_line_commands)} blocks but found {len(blocks)}.\n'
        message += format_command_output(stdout, stderr)

        raise InternalError(message.strip())

    values = blocks[0].split('\n')

    audit_parts = values[0].split(' ', 1)
    audit_status = int(audit_parts[0])
    audit_code = audit_parts[1]

    system_limit = int(values[1])
    hard_limit = int(values[2])
    loginuid = int(values[3]) if values[3] else None

    cgroups = CGroupEntry.loads(blocks[1])
    mounts = MountEntry.loads(blocks[2])

    if hard_limit < MAX_NUM_OPEN_FILES and hard_limit < system_limit and require_docker().command == 'docker':
        # Podman will use the highest possible limits, up to its default of 1M.
        # See: https://github.com/containers/podman/blob/009afb50b308548eb129bc68e654db6c6ad82e7a/pkg/specgen/generate/oci.go#L39-L58
        # Docker limits are less predictable. They could be the system limit or the user's soft limit.
        # If Docker is running as root it should be able to use the system limit.
        # When Docker reports a limit below the preferred value and the system limit, attempt to use the preferred value, up to the system limit.
        options = ['--ulimit', f'nofile={min(system_limit, MAX_NUM_OPEN_FILES)}']
        cmd = ['sh', '-c', 'ulimit -Hn']

        try:
            stdout = run_utility_container(args, 'ansible-test-ulimit', cmd, options)[0]
        except SubprocessError as ex:
            display.warning(str(ex))
        else:
            hard_limit = int(stdout)

    # Check the audit error code from attempting to query the container host's audit status.
    #
    # The following error codes are known to occur:
    #
    # EPERM - Operation not permitted
    # This occurs when the root user runs a container but lacks the AUDIT_WRITE capability.
    # This will cause patched versions of OpenSSH to disconnect after a login succeeds.
    # See: https://src.fedoraproject.org/rpms/openssh/blob/f36/f/openssh-7.6p1-audit.patch
    #
    # EBADF - Bad file number
    # This occurs when the host doesn't support the audit system (the open_audit call fails).
    # This allows SSH logins to succeed despite the failure.
    # See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/netlink.c#L204-L209
    #
    # ECONNREFUSED - Connection refused
    # This occurs when a non-root user runs a container without the AUDIT_WRITE capability.
    # When sending an audit message, libaudit ignores this error condition.
    # This allows SSH logins to succeed despite the failure.
    # See: https://github.com/Distrotech/libaudit/blob/4fc64f79c2a7f36e3ab7b943ce33ab5b013a7782/lib/deprecated.c#L48-L52

    subsystems = set(cgroup.subsystem for cgroup in cgroups)
    mount_types = {mount.path: mount.type for mount in mounts}

    if 'systemd' not in subsystems:
        cgroup_v1 = SystemdControlGroupV1Status.SUBSYSTEM_MISSING
    elif not (mount_type := mount_types.get(pathlib.PurePosixPath('/probe/systemd'))):
        cgroup_v1 = SystemdControlGroupV1Status.FILESYSTEM_NOT_MOUNTED
    elif mount_type != MountType.CGROUP_V1:
        cgroup_v1 = SystemdControlGroupV1Status.MOUNT_TYPE_NOT_CORRECT
    else:
        cgroup_v1 = SystemdControlGroupV1Status.VALID

    cgroup_v2 = mount_types.get(pathlib.PurePosixPath('/probe')) == MountType.CGROUP_V2

    display.info(f'Container host audit status: {audit_code} ({audit_status})', verbosity=1)
    display.info(f'Container host max open files: {hard_limit}', verbosity=1)
    display.info(f'Container loginuid: {loginuid if loginuid is not None else "unavailable"}'
                 f'{" (not set)" if loginuid == LOGINUID_NOT_SET else ""}', verbosity=1)

    if hard_limit < MAX_NUM_OPEN_FILES:
        display.warning(f'Unable to set container max open files to {MAX_NUM_OPEN_FILES}. Using container host limit of {hard_limit} instead.')
    else:
        hard_limit = MAX_NUM_OPEN_FILES

    properties = ContainerHostProperties(
        # The errno (audit_status) is intentionally not exposed here, as it can vary across systems and architectures.
        # Instead, the symbolic name (audit_code) is used, which is resolved inside the container which generated the error.
        # See: https://man7.org/linux/man-pages/man3/errno.3.html
        audit_code=audit_code,
        max_open_files=hard_limit,
        loginuid=loginuid,
        cgroup_v1=cgroup_v1,
        cgroup_v2=cgroup_v2,
    )

    detect_host_properties.properties = properties  # type: ignore[attr-defined]

    return properties