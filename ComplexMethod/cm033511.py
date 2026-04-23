def remove_cgroup_systemd() -> list[pathlib.Path]:
    """Remove the systemd cgroup."""
    dirs = set()

    for sleep_seconds in range(1, 10):
        try:
            for dirpath, dirnames, filenames in os.walk(CGROUP_SYSTEMD, topdown=False):
                for dirname in dirnames:
                    target_path = pathlib.Path(dirpath, dirname)
                    display.info(f'rmdir: {target_path}')
                    dirs.add(target_path)
                    target_path.rmdir()
        except OSError as ex:
            if ex.errno != errno.EBUSY:
                raise

            error = str(ex)
        else:
            break

        display.warning(f'{error} -- sleeping for {sleep_seconds} second(s) before trying again ...')  # pylint: disable=used-before-assignment

        time.sleep(sleep_seconds)

    time.sleep(1)  # allow time for cgroups to be fully removed before unmounting

    run_command('umount', str(CGROUP_SYSTEMD))

    CGROUP_SYSTEMD.rmdir()

    time.sleep(1)  # allow time for cgroup hierarchy to be removed after unmounting

    cgroup = pathlib.Path('/proc/self/cgroup').read_text()

    if 'systemd' in cgroup:
        raise Exception('systemd hierarchy detected')

    return sorted(dirs)