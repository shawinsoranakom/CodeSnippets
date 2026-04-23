def process_options(self, args: list[str], opts: argparse.Namespace) -> None:
        assert self.settings is not None
        try:
            self.settings.setdict(arglist_to_dict(opts.set), priority="cmdline")
        except ValueError:
            raise UsageError(
                "Invalid -s value, use -s NAME=VALUE", print_help=False
            ) from None

        if opts.logfile:
            self.settings.set("LOG_ENABLED", True, priority="cmdline")
            self.settings.set("LOG_FILE", opts.logfile, priority="cmdline")

        if opts.loglevel:
            self.settings.set("LOG_ENABLED", True, priority="cmdline")
            self.settings.set("LOG_LEVEL", opts.loglevel, priority="cmdline")

        if opts.nolog:
            self.settings.set("LOG_ENABLED", False, priority="cmdline")

        if opts.pidfile:
            Path(opts.pidfile).write_text(
                str(os.getpid()) + os.linesep, encoding="utf-8"
            )

        if opts.pdb:
            failure.startDebugMode()