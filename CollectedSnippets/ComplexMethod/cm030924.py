def check_executed_tests(self, output, tests, *, stats,
                             skipped=(), failed=(),
                             env_changed=(), omitted=(),
                             rerun=None, run_no_tests=(),
                             resource_denied=(),
                             randomize=False, parallel=False, interrupted=False,
                             fail_env_changed=False,
                             forever=False, filtered=False):
        if isinstance(tests, str):
            tests = [tests]
        if isinstance(skipped, str):
            skipped = [skipped]
        if isinstance(resource_denied, str):
            resource_denied = [resource_denied]
        if isinstance(failed, str):
            failed = [failed]
        if isinstance(env_changed, str):
            env_changed = [env_changed]
        if isinstance(omitted, str):
            omitted = [omitted]
        if isinstance(run_no_tests, str):
            run_no_tests = [run_no_tests]
        if isinstance(stats, int):
            stats = TestStats(stats)
        if parallel:
            randomize = True

        rerun_failed = []
        if rerun is not None and not env_changed:
            failed = [rerun.name]
            if not rerun.success:
                rerun_failed.append(rerun.name)

        executed = self.parse_executed_tests(output)
        total_tests = list(tests)
        if rerun is not None:
            total_tests.append(rerun.name)
        if randomize:
            self.assertEqual(set(executed), set(total_tests), output)
        else:
            self.assertEqual(executed, total_tests, output)

        def plural(count):
            return 's' if count != 1 else ''

        def list_regex(line_format, tests):
            count = len(tests)
            names = ' '.join(sorted(tests))
            regex = line_format % (count, plural(count))
            regex = r'%s:\n    %s$' % (regex, names)
            return regex

        if skipped:
            regex = list_regex('%s test%s skipped', skipped)
            self.check_line(output, regex)

        if resource_denied:
            regex = list_regex(r'%s test%s skipped \(resource denied\)', resource_denied)
            self.check_line(output, regex)

        if failed:
            regex = list_regex('%s test%s failed', failed)
            self.check_line(output, regex)

        if env_changed:
            regex = list_regex(r'%s test%s altered the execution environment '
                               r'\(env changed\)',
                               env_changed)
            self.check_line(output, regex)

        if omitted:
            regex = list_regex('%s test%s omitted', omitted)
            self.check_line(output, regex)

        if rerun is not None:
            regex = list_regex('%s re-run test%s', [rerun.name])
            self.check_line(output, regex)
            regex = LOG_PREFIX + r"Re-running 1 failed tests in verbose mode"
            self.check_line(output, regex)
            regex = fr"Re-running {rerun.name} in verbose mode"
            if rerun.match:
                regex = fr"{regex} \(matching: {rerun.match}\)"
            self.check_line(output, regex)

        if run_no_tests:
            regex = list_regex('%s test%s run no tests', run_no_tests)
            self.check_line(output, regex)

        good = (len(tests) - len(skipped) - len(resource_denied) - len(failed)
                - len(omitted) - len(env_changed) - len(run_no_tests))
        if good:
            regex = r'%s test%s OK\.' % (good, plural(good))
            if not skipped and not failed and (rerun is None or rerun.success) and good > 1:
                regex = 'All %s' % regex
            self.check_line(output, regex, full=True)

        if interrupted:
            self.check_line(output, 'Test suite interrupted by signal SIGINT.')

        # Total tests
        text = f'run={stats.tests_run:,}'
        if filtered:
            text = fr'{text} \(filtered\)'
        parts = [text]
        if stats.failures:
            parts.append(f'failures={stats.failures:,}')
        if stats.skipped:
            parts.append(f'skipped={stats.skipped:,}')
        line = fr'Total tests: {" ".join(parts)}'
        self.check_line(output, line, full=True)

        # Total test files
        run = len(total_tests) - len(resource_denied)
        if rerun is not None:
            total_failed = len(rerun_failed)
            total_rerun = 1
        else:
            total_failed = len(failed)
            total_rerun = 0
        if interrupted:
            run = 0
        text = f'run={run}'
        if not forever:
            text = f'{text}/{len(tests)}'
        if filtered:
            text = fr'{text} \(filtered\)'
        report = [text]
        for name, ntest in (
            ('failed', total_failed),
            ('env_changed', len(env_changed)),
            ('skipped', len(skipped)),
            ('resource_denied', len(resource_denied)),
            ('rerun', total_rerun),
            ('run_no_tests', len(run_no_tests)),
        ):
            if ntest:
                report.append(f'{name}={ntest}')
        line = fr'Total test files: {" ".join(report)}'
        self.check_line(output, line, full=True)

        # Result
        state = []
        if failed:
            state.append('FAILURE')
        elif fail_env_changed and env_changed:
            state.append('ENV CHANGED')
        if interrupted:
            state.append('INTERRUPTED')
        if not any((good, failed, interrupted, skipped,
                    env_changed, fail_env_changed)):
            state.append("NO TESTS RAN")
        elif not state:
            state.append('SUCCESS')
        state = ', '.join(state)
        if rerun is not None:
            new_state = 'SUCCESS' if rerun.success else 'FAILURE'
            state = f'{state} then {new_state}'
        self.check_line(output, f'Result: {state}', full=True)