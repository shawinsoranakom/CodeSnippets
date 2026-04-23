def run_multiline_interactive_console(
    console: code.InteractiveConsole,
    *,
    future_flags: int = 0,
) -> None:
    from .readline import _setup
    _setup(console.locals)
    if future_flags:
        console.compile.compiler.flags |= future_flags

    more_lines = functools.partial(_more_lines, console)
    input_n = 0

    _is_x_showrefcount_set = sys._xoptions.get("showrefcount")
    _is_pydebug_build = hasattr(sys, "gettotalrefcount")
    show_ref_count = _is_x_showrefcount_set and _is_pydebug_build

    def maybe_run_command(statement: str) -> bool:
        statement = statement.strip()
        if statement in console.locals or statement not in REPL_COMMANDS:
            return False

        reader = _get_reader()
        reader.history.pop()  # skip internal commands in history
        command = REPL_COMMANDS[statement]
        if callable(command):
            # Make sure that history does not change because of commands
            with reader.suspend_history(), reader.suspend_colorization():
                command()
            return True
        return False

    while True:
        try:
            try:
                sys.stdout.flush()
            except Exception:
                pass

            ps1 = getattr(sys, "ps1", ">>> ")
            ps2 = getattr(sys, "ps2", "... ")
            try:
                statement = multiline_input(more_lines, ps1, ps2)
            except EOFError:
                break

            if maybe_run_command(statement):
                continue

            input_name = f"<python-input-{input_n}>"
            more = console.push(_strip_final_indent(statement), filename=input_name, _symbol="single")  # type: ignore[call-arg]
            assert not more
            try:
                append_history_file()
            except (FileNotFoundError, PermissionError, OSError) as e:
                warnings.warn(f"failed to open the history file for writing: {e}")

            input_n += 1
        except KeyboardInterrupt:
            r = _get_reader()
            r.cmpltn_reset()
            if r.input_trans is r.isearch_trans:
                r.do_cmd(("isearch-end", [""]))
            r.pos = len(r.get_unicode())
            r.invalidate_full()
            r.refresh()
            console.write("\nKeyboardInterrupt\n")
            console.resetbuffer()
        except MemoryError:
            console.write("\nMemoryError\n")
            console.resetbuffer()
        except SystemExit:
            raise
        except:
            console.showtraceback()
            console.resetbuffer()
        if show_ref_count:
            console.write(
                f"[{sys.gettotalrefcount()} refs,"
                f" {sys.getallocatedblocks()} blocks]\n"
            )