def get_completions(self, stem: str) -> tuple[list[str], CompletionAction | None]:
        module_completions = self.get_module_completions()
        if module_completions is not None:
            return module_completions
        if len(stem) == 0 and self.more_lines is not None:
            b = self.buffer
            p = self.pos
            while p > 0 and b[p - 1] != "\n":
                p -= 1
            num_spaces = 4 - ((self.pos - p) % 4)
            return [" " * num_spaces], None
        result = []
        function = self.config.readline_completer
        if function is not None:
            try:
                stem = str(stem)  # rlcompleter.py seems to not like unicode
            except UnicodeEncodeError:
                pass  # but feed unicode anyway if we have no choice
            state = 0
            while True:
                try:
                    next = function(stem, state)
                except Exception:
                    break
                if not isinstance(next, str):
                    break
                result.append(next)
                state += 1
            # Emulate readline's sorting using the visible text rather than
            # the raw ANSI escape sequences used for colorized matches.
            result.sort(key=stripcolor)
        return result, None