def get_choices(self, value: str) -> list[str]:
        """Return a list of valid choices based on the given input value."""
        if not value:
            numbers = list(range(1, 10))
        elif self.PATTERN.search(value):
            int_prefix = int(value)
            base = int_prefix * 10
            numbers = [int_prefix] + [base + i for i in range(0, 10)]
        else:
            numbers = []

        # NOTE: the minimum is currently fixed at 1

        if self.maximum is not None:
            numbers = [n for n in numbers if n <= self.maximum]

        return [str(n) for n in numbers]