def cleanup_podman() -> tuple[str, ...]:
    """Cleanup podman processes and files on disk."""
    cleanup = []

    for remaining in range(3, -1, -1):
        processes = [(int(item[0]), item[1]) for item in
                     [item.split(maxsplit=1) for item in run_command('ps', '-A', '-o', 'pid,comm', capture=True).stdout.splitlines()]
                     if pathlib.Path(item[1].split()[0]).name in ('catatonit', 'podman', 'conmon')]

        if not processes:
            break

        for pid, name in processes:
            display.info(f'Killing "{name}" ({pid}) ...')

            try:
                os.kill(pid, signal.SIGTERM if remaining > 1 else signal.SIGKILL)
            except ProcessLookupError:
                pass

            cleanup.append(name)

        time.sleep(1)
    else:
        raise Exception('failed to kill all matching processes')

    uid = pwd.getpwnam(UNPRIVILEGED_USER_NAME).pw_uid

    container_tmp = pathlib.Path(f'/tmp/containers-user-{uid}')
    podman_tmp = pathlib.Path(f'/tmp/podman-run-{uid}')

    user_config = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.config').expanduser()
    user_local = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.local').expanduser()

    if container_tmp.is_dir():
        rmtree(container_tmp)

    if podman_tmp.is_dir():
        rmtree(podman_tmp)

    if user_config.is_dir():
        rmtree(user_config)

    if user_local.is_dir():
        rmtree(user_local)

    return tuple(sorted(set(cleanup)))