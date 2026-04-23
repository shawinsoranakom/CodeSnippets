def handle(self, **options):
        # Execute the command and exit.
        if options["command"]:
            exec(options["command"], {**globals(), **self.get_namespace(**options)})
            return

        # Execute stdin if it has anything to read and exit.
        # Not supported on Windows due to select.select() limitations.
        if (
            sys.platform != "win32"
            and not sys.stdin.isatty()
            and select.select([sys.stdin], [], [], 0)[0]
        ):
            exec(sys.stdin.read(), {**globals(), **self.get_namespace(**options)})
            return

        available_shells = (
            [options["interface"]] if options["interface"] else self.shells
        )

        for shell in available_shells:
            try:
                return getattr(self, shell)(options)
            except ImportError:
                pass
        raise CommandError("Couldn't import {} interface.".format(shell))