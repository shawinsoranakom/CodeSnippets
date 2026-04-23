def _format_failed(self):
        ansi = get_colors()
        red, reset = ansi.BOLD_RED, ansi.RESET
        if self.errors and self.failures:
            le = len(self.errors)
            lf = len(self.failures)
            error_s = "error" + ("s" if le > 1 else "")
            failure_s = "failure" + ("s" if lf > 1 else "")
            return (
                f"{red}{self.test_name} failed "
                f"({le} {error_s}, {lf} {failure_s}){reset}"
            )

        if self.errors:
            le = len(self.errors)
            error_s = "error" + ("s" if le > 1 else "")
            return f"{red}{self.test_name} failed ({le} {error_s}){reset}"

        if self.failures:
            lf = len(self.failures)
            failure_s = "failure" + ("s" if lf > 1 else "")
            return f"{red}{self.test_name} failed ({lf} {failure_s}){reset}"

        return f"{red}{self.test_name} failed{reset}"