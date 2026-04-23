def run_test(scenario: TestScenario) -> TestResult:
    """Run a test scenario and return the test results."""
    display.section(f'Testing {scenario} Started')

    start = time.monotonic()

    integration = ['ansible-test', 'integration', 'split']
    integration_options = ['--target', f'docker:{scenario.container_name}', '--color', '--truncate', '0', '-v']
    target_only_options = []

    if scenario.debug_systemd:
        integration_options.append('--dev-systemd-debug')

    if scenario.probe_cgroups:
        target_only_options = ['--dev-probe-cgroups', str(LOG_PATH)]

    entries = get_container_completion_entries()
    alpine_container = [name for name in entries if name.startswith('alpine')][0]

    commands = [
        # The cgroup probe is only performed for the first test of the target.
        # There's no need to repeat the probe again for the same target.
        # The controller will be tested separately as a target.
        # This ensures that both the probe and no-probe code paths are functional.
        [*integration, *integration_options, *target_only_options],
        # For the split test we'll use Alpine Linux as the controller. There are two reasons for this:
        # 1) It doesn't require the cgroup v1 hack, so we can test a target that doesn't need that.
        # 2) It doesn't require disabling selinux, so we can test a target that doesn't need that.
        [*integration, '--controller', f'docker:{alpine_container}', *integration_options],
    ]

    common_env: dict[str, str] = {}
    test_env: dict[str, str] = {}

    if scenario.engine == 'podman':
        if scenario.user_scenario.remote:
            common_env.update(
                # Podman 4.3.0 has a regression which requires a port for remote connections to work.
                # See: https://github.com/containers/podman/issues/16509
                CONTAINER_HOST=f'ssh://{scenario.user_scenario.remote.name}@localhost:22'
                               f'/run/user/{scenario.user_scenario.remote.pwnam.pw_uid}/podman/podman.sock',
                CONTAINER_SSHKEY=str(pathlib.Path('~/.ssh/id_rsa').expanduser()),  # TODO: add support for ssh + remote when the ssh user is not root
            )

        test_env.update(ANSIBLE_TEST_PREFER_PODMAN='1')

    test_env.update(common_env)

    if scenario.user_scenario.ssh:
        client_become_cmd = ['ssh', f'{scenario.user_scenario.ssh.name}@localhost']
        test_commands = [client_become_cmd + [f'cd ~/ansible; {format_env(test_env)}{sys.executable} bin/{shlex.join(command)}'] for command in commands]
    else:
        client_become_cmd = ['sh', '-c']
        test_commands = [client_become_cmd + [f'{format_env(test_env)}{shlex.join(command)}'] for command in commands]

    prime_storage_command = []

    if scenario.engine == 'podman' and scenario.user_scenario.actual.name == UNPRIVILEGED_USER_NAME:
        # When testing podman we need to make sure that the overlay filesystem is used instead of vfs.
        # Using the vfs filesystem will result in running out of disk space during the tests.
        # To change the filesystem used, the existing storage directory must be removed before "priming" the storage database.
        #
        # Without this change the following message may be displayed:
        #
        #   User-selected graph driver "overlay" overwritten by graph driver "vfs" from database - delete libpod local files to resolve
        #
        # However, with this change it may be replaced with the following message:
        #
        #   User-selected graph driver "vfs" overwritten by graph driver "overlay" from database - delete libpod local files to resolve

        actual_become_cmd = ['ssh', f'{scenario.user_scenario.actual.name}@localhost']
        prime_storage_command = actual_become_cmd + prepare_prime_podman_storage()

    message = ''

    if scenario.expose_cgroup_version == 1:
        prepare_cgroup_systemd(scenario.user_scenario.actual.name, scenario.engine)

    try:
        if prime_storage_command:
            retry_command(lambda: run_command(*prime_storage_command), retry_any_error=True)

        if scenario.disable_selinux:
            run_command('setenforce', 'permissive')

        if scenario.enable_sha1:
            run_command('update-crypto-policies', '--set', 'DEFAULT:SHA1')

        if scenario.disable_apparmor_profile_unix_chkpwd:
            os.symlink('/etc/apparmor.d/unix-chkpwd', '/etc/apparmor.d/disable/unix-chkpwd')
            run_command('apparmor_parser', '-R', '/etc/apparmor.d/unix-chkpwd')

        for test_command in test_commands:
            def run_test_command() -> SubprocessResult:
                if os_release.id == 'alpine' and scenario.user_scenario.actual.name != 'root':
                    # Make sure rootless networking works on Alpine.
                    # NOTE: The path used below differs slightly from the referenced issue.
                    # See: https://gitlab.alpinelinux.org/alpine/aports/-/issues/16137
                    actual_pwnam = scenario.user_scenario.actual.pwnam
                    root_path = pathlib.Path(f'/tmp/storage-run-{actual_pwnam.pw_uid}')
                    run_path = root_path / 'containers/networks/rootless-netns/run'
                    run_path.mkdir(mode=0o755, parents=True, exist_ok=True)

                    while run_path.is_relative_to(root_path):
                        os.chown(run_path, actual_pwnam.pw_uid, actual_pwnam.pw_gid)
                        run_path = run_path.parent

                return run_command(*test_command)

            retry_command(run_test_command)
    except SubprocessError as ex:
        message = str(ex)
        display.error(f'{scenario} {message}')
    finally:
        if scenario.disable_apparmor_profile_unix_chkpwd:
            os.unlink('/etc/apparmor.d/disable/unix-chkpwd')
            run_command('apparmor_parser', '/etc/apparmor.d/unix-chkpwd')

        if scenario.enable_sha1:
            run_command('update-crypto-policies', '--set', 'DEFAULT')

        if scenario.disable_selinux:
            run_command('setenforce', 'enforcing')

        if scenario.expose_cgroup_version == 1:
            dirs = remove_cgroup_systemd()
        else:
            dirs = list_group_systemd()

        cleanup_command = [scenario.engine, 'rmi', '-f', scenario.image]

        try:
            retry_command(lambda: run_command(*client_become_cmd + [f'{format_env(common_env)}{shlex.join(cleanup_command)}']), retry_any_error=True)
        except SubprocessError as ex:
            display.error(str(ex))

        cleanup = cleanup_podman() if scenario.engine == 'podman' else tuple()

    finish = time.monotonic()
    duration = datetime.timedelta(seconds=int(finish - start))

    display.section(f'Testing {scenario} Completed in {duration}')

    return TestResult(
        scenario=scenario,
        message=message,
        cleanup=cleanup,
        duration=duration,
        cgroup_dirs=tuple(str(path) for path in dirs),
    )