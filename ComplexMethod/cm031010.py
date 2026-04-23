def display_result(self, tests: TestTuple, quiet: bool, print_slowest: bool) -> None:
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        if print_slowest:
            self.test_times.sort(reverse=True)
            print()
            print(f"{yellow}10 slowest tests:{reset}")
            for test_time, test in self.test_times[:10]:
                print(f"- {test}: {format_duration(test_time)}")

        all_tests = []
        omitted = set(tests) - self.get_executed()

        # less important
        all_tests.append(
            (sorted(omitted), "test", f"{yellow}{{}} omitted:{reset}")
        )
        if not quiet:
            all_tests.append(
                (self.skipped, "test", f"{yellow}{{}} skipped:{reset}")
            )
            all_tests.append(
                (
                    self.resource_denied,
                    "test",
                    f"{yellow}{{}} skipped (resource denied):{reset}",
                )
            )
        all_tests.append(
            (self.run_no_tests, "test", f"{yellow}{{}} run no tests:{reset}")
        )

        # more important
        all_tests.append(
            (
                self.env_changed,
                "test",
                f"{yellow}{{}} altered the execution environment (env changed):{reset}",
            )
        )
        all_tests.append((self.rerun, "re-run test", f"{yellow}{{}}:{reset}"))
        all_tests.append((self.bad, "test", f"{red}{{}} failed:{reset}"))

        for tests_list, count_text, title_format in all_tests:
            if tests_list:
                print()
                count_text = count(len(tests_list), count_text)
                print(title_format.format(count_text))
                printlist(tests_list)

        if self.good and not quiet:
            print()
            text = count(len(self.good), "test")
            text = f"{green}{text} OK.{reset}"
            if self.is_all_good() and len(self.good) > 1:
                text = f"All {text}"
            print(text)

        if self.interrupted:
            print()
            print(f"{yellow}Test suite interrupted by signal SIGINT.{reset}")