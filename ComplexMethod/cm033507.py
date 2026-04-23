def main() -> None:
    """Main program entry point."""
    display.section('Startup check')

    try:
        bootstrap_type = pathlib.Path('/etc/ansible-test.bootstrap').read_text().strip()
    except FileNotFoundError:
        bootstrap_type = 'undefined'

    display.info(f'Bootstrap type: {bootstrap_type}')

    if bootstrap_type != 'remote':
        display.warning('Skipping destructive test on system which is not an ansible-test remote provisioned instance.')
        return

    display.info(f'UID: {UID} / {LOGINUID}')

    if UID != 0:
        raise Exception('This test must be run as root.')

    if not LOGINUID_MISMATCH:
        if LOGINUID is None:
            display.warning('Tests involving loginuid mismatch will be skipped on this host since it does not have audit support.')
        elif LOGINUID == LOGINUID_NOT_SET:
            display.warning('Tests involving loginuid mismatch will be skipped on this host since it is not set.')
        elif LOGINUID == 0:
            raise Exception('Use sudo, su, etc. as a non-root user to become root before running this test.')
        else:
            raise Exception()

    display.section(f'Bootstrapping {os_release}')

    bootstrapper = Bootstrapper.init()
    bootstrapper.run()

    result_dir = LOG_PATH

    if result_dir.exists():
        shutil.rmtree(result_dir)

    result_dir.mkdir()
    result_dir.chmod(0o777)

    scenarios = get_test_scenarios()
    results = [run_test(scenario) for scenario in scenarios]
    error_total = 0

    for name in sorted(result_dir.glob('*.log')):
        lines = name.read_text().strip().splitlines()
        error_count = len([line for line in lines if line.startswith('FAIL: ')])
        error_total += error_count

        display.section(f'Log ({error_count=}/{len(lines)}): {name.name}')

        for line in lines:
            if line.startswith('FAIL: '):
                display.show(line, display.RED)
            else:
                display.show(line)

    error_count = len([result for result in results if result.message])
    error_total += error_count

    duration = datetime.timedelta(seconds=int(sum(result.duration.total_seconds() for result in results)))

    display.section(f'Test Results ({error_count=}/{len(results)}) [{duration}]')

    for result in results:
        notes = f' <cleanup: {", ".join(result.cleanup)}>' if result.cleanup else ''

        if result.cgroup_dirs:
            notes += f' <cgroup_dirs: {len(result.cgroup_dirs)}>'

        notes += f' [{result.duration}]'

        if result.message:
            display.show(f'FAIL: {result.scenario} {result.message}{notes}', display.RED)
        elif result.duration.total_seconds() >= 90:
            display.show(f'SLOW: {result.scenario}{notes}', display.YELLOW)
        else:
            display.show(f'PASS: {result.scenario}{notes}')

    if error_total:
        sys.exit(1)