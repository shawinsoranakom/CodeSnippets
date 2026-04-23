def summarize(self, verbose=None):
        """
        Print a summary of all the test cases that have been run by
        this DocTestRunner, and return a TestResults instance.

        The optional `verbose` argument controls how detailed the
        summary is.  If the verbosity is not specified, then the
        DocTestRunner's verbosity is used.
        """
        if verbose is None:
            verbose = self._verbose

        notests, passed, failed = [], [], []
        total_tries = total_failures = total_skips = 0

        for name, (failures, tries, skips) in self._stats.items():
            assert failures <= tries
            total_tries += tries
            total_failures += failures
            total_skips += skips

            if tries == 0:
                notests.append(name)
            elif failures == 0:
                passed.append((name, tries))
            else:
                failed.append((name, (failures, tries, skips)))

        ansi = _colorize.get_colors()
        bold_green = ansi.BOLD_GREEN
        bold_red = ansi.BOLD_RED
        green = ansi.GREEN
        red = ansi.RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        if verbose:
            if notests:
                print(f"{_n_items(notests)} had no tests:")
                notests.sort()
                for name in notests:
                    print(f"    {name}")

            if passed:
                print(f"{green}{_n_items(passed)} passed all tests:{reset}")
                for name, count in sorted(passed):
                    s = "" if count == 1 else "s"
                    print(f" {green}{count:3d} test{s} in {name}{reset}")

        if failed:
            print(f"{red}{self.DIVIDER}{reset}")
            print(f"{_n_items(failed)} had failures:")
            for name, (failures, tries, skips) in sorted(failed):
                print(f" {failures:3d} of {tries:3d} in {name}")

        if verbose:
            s = "" if total_tries == 1 else "s"
            print(f"{total_tries} test{s} in {_n_items(self._stats)}.")

            and_f = (
                f" and {red}{total_failures} failed{reset}"
                if total_failures else ""
            )
            print(f"{green}{total_tries - total_failures} passed{reset}{and_f}.")

        if total_failures:
            s = "" if total_failures == 1 else "s"
            msg = f"{bold_red}***Test Failed*** {total_failures} failure{s}{reset}"
            if total_skips:
                s = "" if total_skips == 1 else "s"
                msg = f"{msg} and {yellow}{total_skips} skipped test{s}{reset}"
            print(f"{msg}.")
        elif verbose:
            print(f"{bold_green}Test passed.{reset}")

        return TestResults(total_failures, total_tries, skipped=total_skips)