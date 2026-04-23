def attr_matches(self, text):
        try:
            expr, attr, names, values = self._attr_matches(text)
        except ValueError:
            return []

        if not names:
            return []

        if len(names) == 1:
            # No coloring: when returning a single completion, readline
            # inserts it directly into the prompt, so ANSI codes would
            # appear as literal characters.
            return [self._callable_attr_postfix(values[0], f'{expr}.{names[0]}')]

        prefix = commonprefix(names)
        if prefix and prefix != attr:
            return [f'{expr}.{prefix}']  # autocomplete prefix

        names = [f'{expr}.{name}' for name in names]
        if self.use_colors:
            return self.colorize_matches(names, values)
        return names