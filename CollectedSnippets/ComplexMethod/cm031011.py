def display_summary(self, first_runtests: RunTests, filtered: bool) -> None:
        # Total tests
        ansi = get_colors()
        red, reset, yellow = ansi.RED, ansi.RESET, ansi.YELLOW

        stats = self.stats
        text = f'run={stats.tests_run:,}'
        if filtered:
            text = f"{text} (filtered)"
        report = [text]
        if stats.failures:
            report.append(f'{red}failures={stats.failures:,}{reset}')
        if stats.skipped:
            report.append(f'{yellow}skipped={stats.skipped:,}{reset}')
        print(f"Total tests: {' '.join(report)}")

        # Total test files
        all_tests = [self.good, self.bad, self.rerun,
                     self.skipped,
                     self.env_changed, self.run_no_tests]
        run = sum(map(len, all_tests))
        text = f'run={run}'
        if not first_runtests.forever:
            ntest = len(first_runtests.tests)
            text = f"{text}/{ntest}"
        if filtered:
            text = f"{text} (filtered)"
        report = [text]
        for name, tests, color in (
            ('failed', self.bad, red),
            ('env_changed', self.env_changed, yellow),
            ('skipped', self.skipped, yellow),
            ('resource_denied', self.resource_denied, yellow),
            ('rerun', self.rerun, yellow),
            ('run_no_tests', self.run_no_tests, yellow),
        ):
            if tests:
                report.append(f'{color}{name}={len(tests)}{reset}')
        print(f"Total test files: {' '.join(report)}")