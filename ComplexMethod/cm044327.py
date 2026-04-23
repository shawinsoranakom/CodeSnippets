def _process_arguments(self) -> None:
        """ Process any cli arguments and dummy in cli arguments if calling from updater. """
        args = sys.argv[:]
        if self.updater:
            get_backend = T.cast("lib_utils",  # type:ignore[attr-defined,valid-type]
                                 import_module("lib.utils")).get_backend
            args.append(f"--{get_backend()}")
        logger.debug(args)
        if self.system.is_macos and self.system.machine == "arm64":
            self.set_backend("apple_silicon")
            self.set_requirements("apple-silicon")
        for arg in args:
            if arg == "--installer":
                self.is_installer = True
                continue
            if arg == "--dev":
                self.include_dev_tools = True
                continue
            if not self.backend and arg.startswith("--"):
                self._parse_backend_from_cli(arg[2:])