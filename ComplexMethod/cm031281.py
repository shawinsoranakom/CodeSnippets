def run(self):
        global return_code

        try:
            if not sys.flags.quiet:
                banner = (
                    f'asyncio REPL {sys.version} on {sys.platform}\n'
                    f'Use "await" directly instead of "asyncio.run()".\n'
                    f'Type "help", "copyright", "credits" or "license" '
                    f'for more information.\n'
                )

                console.write(banner)

            if not sys.flags.isolated and (startup_path := os.getenv("PYTHONSTARTUP")):
                sys.audit("cpython.run_startup", startup_path)

                import tokenize
                with tokenize.open(startup_path) as f:
                    startup_code = compile(f.read(), startup_path, "exec")
                    exec(startup_code, console.locals)

            ps1 = getattr(sys, "ps1", ">>> ")
            if CAN_USE_PYREPL:
                theme = get_theme().syntax
                ps1 = f"{theme.prompt}{ps1}{theme.reset}"
                import_line = f'{theme.keyword}import{theme.reset} asyncio'
            else:
                import_line = "import asyncio"
            console.write(f"{ps1}{import_line}\n")

            if CAN_USE_PYREPL:
                from _pyrepl.simple_interact import (
                    run_multiline_interactive_console,
                )
                try:
                    sys.ps1 = ps1
                    run_multiline_interactive_console(console)
                except SystemExit:
                    # expected via the `exit` and `quit` commands
                    pass
                except BaseException:
                    # unexpected issue
                    console.showtraceback()
                    console.write("Internal error, ")
                    return_code = 1
            else:
                console.interact(banner="", exitmsg="")
        finally:
            warnings.filterwarnings(
                'ignore',
                message=r'^coroutine .* was never awaited$',
                category=RuntimeWarning)

            loop.call_soon_threadsafe(loop.stop)