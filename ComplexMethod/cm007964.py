def update_requirements(
    upgrade_only: str | None = None,
    verify: bool = False,
) -> dict[str, tuple[str | None, str | None]]:
    # Are we upgrading all packages or only one (e.g. 'yt-dlp-ejs' or 'protobug')?
    upgrade_arg = f'--upgrade-package={upgrade_only}' if upgrade_only else '--upgrade'

    pyproject_text = PYPROJECT_PATH.read_text()
    pyproject_toml = parse_toml(pyproject_text)
    extras = pyproject_toml['project']['optional-dependencies']

    # Remove pinned extras so they don't muck up the lockfile during generation/upgrade
    for pinned_extra_name in PINNED_EXTRAS:
        extras.pop(pinned_extra_name, None)

    # Write an intermediate pyproject.toml to use for generating lockfile and bundle requirements
    modify_and_write_pyproject(pyproject_text, table_name=EXTRAS_TABLE, table=extras)

    old_lock = None
    if LOCKFILE_PATH.is_file():
        old_lock = parse_toml(LOCKFILE_PATH.read_text())

    # If verifying, set UV_EXCLUDE_NEWER env var with the last timestamp recorded in uv.lock
    env = None
    if verify or upgrade_only in pyproject_toml['tool']['uv']['exclude-newer-package']:
        env = os.environ.copy()
        env['UV_EXCLUDE_NEWER'] = old_lock['options']['exclude-newer']
        print(f'Setting UV_EXCLUDE_NEWER={env["UV_EXCLUDE_NEWER"]}', file=sys.stderr)

    # Generate/upgrade lockfile
    print(f'Running: uv lock {upgrade_arg}', file=sys.stderr)
    run_process('uv', 'lock', upgrade_arg, env=env)

    # Record diff in uv.lock packages
    old_packages = get_lock_packages(old_lock) if old_lock else {}
    new_packages = get_lock_packages(parse_toml(LOCKFILE_PATH.read_text()))
    all_updates = package_diff_dict(old_packages, new_packages)

    # Update Windows PyInstaller requirements; need to compare before & after .txt's for reporting
    if not upgrade_only or upgrade_only.lower() == 'pyinstaller':
        info = fetch_latest_github_release('yt-dlp', 'Pyinstaller-Builds')
        for target_suffix, asset_tag in PYINSTALLER_BUILDS_TARGETS.items():
            asset_info = next(asset for asset in info['assets'] if asset_tag in asset['name'])
            pyinstaller_version = parse_version_from_dist(
                asset_info['name'], 'pyinstaller', require=True)
            pyinstaller_builds_deps = run_pip_compile(
                '--no-emit-package=pyinstaller',
                upgrade_arg,
                input_line=f'pyinstaller=={pyinstaller_version}',
                env=env)
            requirements_path = REQUIREMENTS_PATH / REQS_OUTPUT_TMPL.format(target_suffix)
            if requirements_path.is_file():
                old_requirements_txt = requirements_path.read_text()
            else:
                old_requirements_txt = ''

            new_requirements_txt = PYINSTALLER_BUILDS_TMPL.format(
                pyinstaller_builds_deps, asset_info['browser_download_url'], asset_info['digest'])
            requirements_path.write_text(new_requirements_txt)
            all_updates.update(evaluate_requirements_txt(old_requirements_txt, new_requirements_txt))

    # Export bundle requirements; any updates to these are already recorded w/ uv.lock package diff
    for target_suffix, target in BUNDLE_TARGETS.items():
        run_uv_export(
            extras=target.extras,
            groups=target.groups,
            prune_packages=target.prune_packages,
            omit_packages=target.omit_packages,
            output_file=REQUIREMENTS_PATH / REQS_OUTPUT_TMPL.format(target_suffix))

    # Export group requirements; any updates to these are already recorded w/ uv.lock package diff
    for group in ('build',):
        run_uv_export(
            groups=[group],
            output_file=REQUIREMENTS_PATH / REQS_OUTPUT_TMPL.format(group))

    # Compile requirements for single packages; need to compare before & after .txt's for reporting
    for package in ('pip',):
        requirements_path = REQUIREMENTS_PATH / REQS_OUTPUT_TMPL.format(package)
        if requirements_path.is_file():
            old_requirements_txt = requirements_path.read_text()
        else:
            old_requirements_txt = ''

        run_pip_compile(
            upgrade_arg,
            input_line=package,
            output_file=REQUIREMENTS_PATH / REQS_OUTPUT_TMPL.format(package),
            env=env)

        new_requirements_txt = requirements_path.read_text()
        all_updates.update(evaluate_requirements_txt(old_requirements_txt, new_requirements_txt))

    # Generate new pinned extras; any updates to these are already recorded w/ uv.lock package diff
    for pinned_name, extra_name in PINNED_EXTRAS.items():
        extras[pinned_name] = run_uv_export(extras=[extra_name], bare=True).splitlines()

    # Write the finalized pyproject.toml
    modify_and_write_pyproject(pyproject_text, table_name=EXTRAS_TABLE, table=extras)

    return all_updates