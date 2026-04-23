def compare(self) -> None:
        if self.check_dtype and type(self.actual) is not type(self.expected):
            self._fail(
                AssertionError,
                f"The (d)types do not match: {type(self.actual)} != {type(self.expected)}.",
            )

        if self.actual == self.expected:
            return

        if self.equal_nan and cmath.isnan(self.actual) and cmath.isnan(self.expected):
            return

        abs_diff = abs(self.actual - self.expected)
        tolerance = self.atol + self.rtol * abs(self.expected)

        if cmath.isfinite(abs_diff) and abs_diff <= tolerance:
            return

        self._fail(
            AssertionError,
            make_scalar_mismatch_msg(
                self.actual, self.expected, rtol=self.rtol, atol=self.atol
            ),
        )