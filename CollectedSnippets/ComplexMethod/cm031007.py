def get_state(self, fail_env_changed: bool) -> str:
        state = []
        ansi = get_colors()
        green = ansi.GREEN
        red = ansi.BOLD_RED
        reset = ansi.RESET
        yellow = ansi.YELLOW
        if self.bad:
            state.append(f"{red}FAILURE{reset}")
        elif fail_env_changed and self.env_changed:
            state.append(f"{yellow}ENV CHANGED{reset}")
        elif self.no_tests_run():
            state.append(f"{yellow}NO TESTS RAN{reset}")

        if self.interrupted:
            state.append(f"{yellow}INTERRUPTED{reset}")
        if self.worker_bug:
            state.append(f"{red}WORKER BUG{reset}")
        if not state:
            state.append(f"{green}SUCCESS{reset}")

        return ', '.join(state)