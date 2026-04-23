def command_sanity(args: SanityConfig) -> None:
    """Run sanity tests."""
    create_result_directories(args)

    target_configs = t.cast(list[PosixConfig], args.targets)
    target_versions: dict[str, PosixConfig] = {target.python.version: target for target in target_configs}

    handle_layout_messages(data_context().content.sanity_messages)

    changes = get_changes_filter(args)
    require = args.require + changes
    targets = SanityTargets.create(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    tests = list(sanity_get_tests())

    if args.test:
        disabled = []
        tests = [target for target in tests if target.name in args.test]
    else:
        disabled = [target.name for target in tests if not target.enabled and not args.allow_disabled]
        tests = [target for target in tests if target.enabled or args.allow_disabled]

    if args.skip_test:
        tests = [target for target in tests if target.name not in args.skip_test]

    if not args.host_path:
        for test in tests:
            test.origin_hook(args)

    targets_use_pypi = any(isinstance(test, SanityMultipleVersion) and test.needs_pypi for test in tests) and not args.list_tests
    host_state = prepare_profiles(args, targets_use_pypi=targets_use_pypi)  # sanity

    get_content_config(args)  # make sure content config has been parsed prior to delegation

    if args.delegate:
        raise Delegate(host_state=host_state, require=changes, exclude=args.exclude)

    install_requirements(args, host_state.controller_profile, host_state.controller_profile.python)  # sanity
    configure_pypi_proxy(args, host_state.controller_profile)  # sanity

    if disabled:
        display.warning('Skipping tests disabled by default without --allow-disabled: %s' % ', '.join(sorted(disabled)))

    target_profiles: dict[str, PosixProfile] = {profile.config.python.version: profile for profile in host_state.targets(PosixProfile)}

    total = 0
    failed = []

    result: t.Optional[TestResult]

    for test in tests:
        if args.list_tests:
            print(test.name)  # display goes to stderr, this should be on stdout
            continue

        for version in SUPPORTED_PYTHON_VERSIONS:
            options = ''

            if isinstance(test, SanityMultipleVersion):
                if version not in target_versions and version not in args.host_settings.skipped_python_versions:
                    continue  # version was not requested, skip it silently
            else:
                if version != args.controller_python.version:
                    continue  # only multi-version sanity tests use target versions, the rest use the controller version

            if test.supported_python_versions and version not in test.supported_python_versions:
                result = SanitySkipped(test.name, version)
                result.reason = f'Skipping sanity test "{test.name}" on Python {version} because it is unsupported.' \
                                f' Supported Python versions: {", ".join(test.supported_python_versions)}'
            else:
                if isinstance(test, SanityMultipleVersion):
                    settings = test.load_processor(args, version)
                elif isinstance(test, SanitySingleVersion):
                    settings = test.load_processor(args)
                elif isinstance(test, SanityVersionNeutral):
                    settings = test.load_processor(args)
                else:
                    raise Exception('Unsupported test type: %s' % type(test))

                all_targets = list(targets.targets)

                if test.all_targets:
                    usable_targets = list(targets.targets)
                elif test.no_targets:
                    usable_targets = []
                else:
                    usable_targets = list(targets.include)

                all_targets = SanityTargets.filter_and_inject_targets(test, all_targets)
                usable_targets = SanityTargets.filter_and_inject_targets(test, usable_targets)

                usable_targets = sorted(test.filter_targets_by_version(args, list(usable_targets), version))
                usable_targets = settings.filter_skipped_targets(usable_targets)
                sanity_targets = SanityTargets(tuple(all_targets), tuple(usable_targets))

                test_needed = bool(usable_targets or test.no_targets or args.prime_venvs)
                result = None

                if test_needed and version in args.host_settings.skipped_python_versions:
                    # Deferred checking of Python availability. Done here since it is now known to be required for running the test.
                    # Earlier checking could cause a spurious warning to be generated for a collection which does not support the Python version.
                    # If the user specified a Python version, an error will be generated before reaching this point when the Python interpreter is not found.
                    result = SanitySkipped(test.name, version)
                    result.reason = f'Skipping sanity test "{test.name}" on Python {version} because it could not be found.'

                if not result:
                    if isinstance(test, SanityMultipleVersion):
                        display.info(f'Running sanity test "{test.name}" on Python {version}')
                    else:
                        display.info(f'Running sanity test "{test.name}"')

                if test_needed and not result:
                    if isinstance(test, SanityMultipleVersion):
                        # multi-version sanity tests handle their own requirements (if any) and use the target python
                        test_profile = target_profiles[version]
                        result = test.test(args, sanity_targets, test_profile.python)
                        options = ' --python %s' % version
                    elif isinstance(test, SanitySingleVersion):
                        # single version sanity tests use the controller python
                        test_profile = host_state.controller_profile
                        virtualenv_python = create_sanity_virtualenv(args, test_profile.python, test.name)

                        if virtualenv_python:
                            virtualenv_yaml = args.explain or check_sanity_virtualenv_yaml(virtualenv_python)

                            if test.require_libyaml and not virtualenv_yaml:
                                result = SanitySkipped(test.name)
                                result.reason = f'Skipping sanity test "{test.name}" on Python {version} due to missing libyaml support in PyYAML.'
                            else:
                                if virtualenv_yaml is False:
                                    display.warning(f'Sanity test "{test.name}" on Python {version} may be slow due to missing libyaml support in PyYAML.')

                                if args.prime_venvs:
                                    result = SanitySkipped(test.name)
                                else:
                                    result = test.test(args, sanity_targets, virtualenv_python)
                        else:
                            result = SanitySkipped(test.name, version)
                            result.reason = f'Skipping sanity test "{test.name}" on Python {version} due to missing virtual environment support.'
                    elif isinstance(test, SanityVersionNeutral):
                        if args.prime_venvs:
                            result = SanitySkipped(test.name)
                        else:
                            # version neutral sanity tests handle their own requirements (if any)
                            result = test.test(args, sanity_targets)
                    else:
                        raise Exception('Unsupported test type: %s' % type(test))
                elif result:
                    pass
                else:
                    result = SanitySkipped(test.name, version)

            result.write(args)

            total += 1

            if isinstance(result, SanityFailure):
                failed.append(result.test + options)

    controller = args.controller

    if created_venvs and isinstance(controller, DockerConfig) and controller.name == 'default' and not args.prime_venvs:
        names = ', '.join(created_venvs)
        display.warning(f'The following sanity test virtual environments are out-of-date in the "default" container: {names}')

    if failed:
        message = 'The %d sanity test(s) listed below (out of %d) failed. See error output above for details.\n%s' % (
            len(failed), total, '\n'.join(failed))

        if args.failure_ok:
            display.error(message)
        else:
            raise ApplicationError(message)