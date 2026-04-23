def add_arguments(self, actions: Iterable[Action]):
        for action in actions:
            if len(action.option_strings) == 0 or "--help" in action.option_strings:
                continue

            option_strings = f"`{'`, `'.join(action.option_strings)}`"
            heading_md = f"{self._argument_heading_prefix} {option_strings}\n\n"
            self._markdown_output.append(heading_md)

            if action.choices or isinstance(action.metavar, list | tuple):
                choices_iterable = action.choices or action.metavar
                choices = f"`{'`, `'.join(str(c) for c in choices_iterable)}`"
                self._markdown_output.append(f":   Possible choices: {choices}\n\n")

            if action.help:
                help_dd = ":" + textwrap.indent(action.help, "    ")[1:]
                self._markdown_output.append(f"{help_dd}\n\n")

            # None usually means the default is determined at runtime
            if (default := action.default) != SUPPRESS and default is not None:
                # Make empty string defaults visible
                if default == "":
                    default = '""'
                self._markdown_output.append(f":   Default: `{default}`\n\n")