def runsource(self, source, filename="<input>", symbol="single"):
        """Override runsource, the core of the InteractiveConsole REPL.

        Return True if more input is needed; buffering is done automatically.
        Return False if input is a complete statement ready for execution.
        """
        theme = get_theme(force_no_color=not self._use_color)

        if not source or source.isspace():
            return False
        # Remember to update CLI_COMMANDS in _completer.py
        if source[0] == ".":
            match source[1:].strip():
                case "version":
                    print(sqlite3.sqlite_version)
                case "help":
                    t = theme.syntax
                    print(f"Enter SQL code or one of the below commands, and press enter.\n\n"
                          f"{t.builtin}.version{t.reset}    Print underlying SQLite library version\n"
                          f"{t.builtin}.help{t.reset}       Print this help message\n"
                          f"{t.builtin}.quit{t.reset}       Exit the CLI, equivalent to CTRL-D\n")
                case "quit":
                    sys.exit(0)
                case "":
                    pass
                case _ as unknown:
                    t = theme.traceback
                    self.write(f'{t.type}Error{t.reset}: {t.message}unknown '
                               f'command: "{unknown}"{t.reset}\n')
        else:
            if not sqlite3.complete_statement(source):
                return True
            execute(self._cur, source, theme=theme)
        return False