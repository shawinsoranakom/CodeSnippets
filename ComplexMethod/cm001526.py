def apply(self, x):
        res = ''

        for m in re_pattern.finditer(x):
            text, pattern = m.groups()

            if pattern is None:
                res += text
                continue

            pattern_args = []
            while True:
                m = re_pattern_arg.match(pattern)
                if m is None:
                    break

                pattern, arg = m.groups()
                pattern_args.insert(0, arg)

            fun = self.replacements.get(pattern.lower())
            if fun is not None:
                try:
                    replacement = fun(self, *pattern_args)
                except Exception:
                    replacement = None
                    errors.report(f"Error adding [{pattern}] to filename", exc_info=True)

                if replacement == NOTHING_AND_SKIP_PREVIOUS_TEXT:
                    continue
                elif replacement is not None:
                    res += text + str(replacement)
                    continue

            res += f'{text}[{pattern}]'

        return res