def autocomplete(self):
        """
        Output completion suggestions for BASH.

        The output of this function is passed to BASH's `COMPREPLY` variable
        and treated as completion suggestions. `COMPREPLY` expects a space
        separated string as the result.

        The `COMP_WORDS` and `COMP_CWORD` BASH environment variables are used
        to get information about the cli input. Please refer to the BASH
        man-page for more information about this variables.

        Subcommand options are saved as pairs. A pair consists of
        the long option string (e.g. '--exclude') and a boolean
        value indicating if the option requires arguments. When printing to
        stdout, an equal sign is appended to options which require arguments.

        Note: If debugging this function, it is recommended to write the debug
        output in a separate file. Otherwise the debug output will be treated
        and formatted as potential completion suggestions.
        """
        # Don't complete if user hasn't sourced bash_completion file.
        if "DJANGO_AUTO_COMPLETE" not in os.environ:
            return

        cwords = os.environ["COMP_WORDS"].split()[1:]
        cword = int(os.environ["COMP_CWORD"])

        try:
            curr = cwords[cword - 1]
        except IndexError:
            curr = ""

        subcommands = [*get_commands(), "help"]
        options = [("--help", False)]

        # subcommand
        if cword == 1:
            print(" ".join(sorted(filter(lambda x: x.startswith(curr), subcommands))))
        # subcommand options
        # special case: the 'help' subcommand has no options
        elif cwords[0] in subcommands and cwords[0] != "help":
            subcommand_cls = self.fetch_command(cwords[0])
            # special case: add the names of installed apps to options
            if cwords[0] in ("dumpdata", "sqlmigrate", "sqlsequencereset", "test"):
                try:
                    app_configs = apps.get_app_configs()
                    # Get the last part of the dotted path as the app name.
                    options.extend((app_config.label, 0) for app_config in app_configs)
                except ImportError:
                    # Fail silently if DJANGO_SETTINGS_MODULE isn't set. The
                    # user will find out once they execute the command.
                    pass
            parser = subcommand_cls.create_parser("", cwords[0])
            options.extend(
                (min(s_opt.option_strings), s_opt.nargs != 0)
                for s_opt in parser._actions
                if s_opt.option_strings
            )
            # filter out previously specified options from available options
            prev_opts = {x.split("=")[0] for x in cwords[1 : cword - 1]}
            options = (opt for opt in options if opt[0] not in prev_opts)

            # filter options by current input
            options = sorted((k, v) for k, v in options if k.startswith(curr))
            for opt_label, require_arg in options:
                # append '=' to options which require args
                if require_arg:
                    opt_label += "="
                print(opt_label)
        # Exit code of the bash completion function is never passed back to
        # the user, so it's safe to always exit with 0.
        # For more details see #25420.
        sys.exit(0)