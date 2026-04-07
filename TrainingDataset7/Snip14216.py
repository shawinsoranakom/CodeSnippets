def __iter__(self):
        choices, other = tee(self.choices)
        if not any(value in ("", None) for value, _ in flatten_choices(other)):
            yield from self.blank_choice
        yield from choices