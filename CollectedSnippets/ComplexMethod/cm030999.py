def __str__(self) -> str:
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW

        match self.state:
            case State.PASSED:
                return f"{green}{self.test_name} passed{reset}"
            case State.FAILED:
                return f"{red}{self._format_failed()}{reset}"
            case State.SKIPPED:
                return f"{yellow}{self.test_name} skipped{reset}"
            case State.UNCAUGHT_EXC:
                return (
                    f"{red}{self.test_name} failed (uncaught exception){reset}"
                )
            case State.REFLEAK:
                return f"{red}{self.test_name} failed (reference leak){reset}"
            case State.ENV_CHANGED:
                return f"{red}{self.test_name} failed (env changed){reset}"
            case State.RESOURCE_DENIED:
                return f"{yellow}{self.test_name} skipped (resource denied){reset}"
            case State.INTERRUPTED:
                return f"{yellow}{self.test_name} interrupted{reset}"
            case State.WORKER_FAILED:
                return (
                    f"{red}{self.test_name} worker non-zero exit code{reset}"
                )
            case State.WORKER_BUG:
                return f"{red}{self.test_name} worker bug{reset}"
            case State.DID_NOT_RUN:
                return f"{yellow}{self.test_name} ran no tests{reset}"
            case State.TIMEOUT:
                assert self.duration is not None, "self.duration is None"
                return f"{self.test_name} timed out ({format_duration(self.duration)})"
            case _:
                raise ValueError(
                    f"{red}unknown result state: {{state!r}}{reset}"
                )