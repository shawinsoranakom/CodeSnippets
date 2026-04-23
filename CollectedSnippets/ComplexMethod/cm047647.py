def _parse_config(self, args=None):
        # preprocess the args to add support for nargs='?'
        for arg_no, arg in enumerate(args or ()):
            if option := self.optional_options.get(arg):
                if arg_no == len(args) - 1 or args[arg_no + 1].startswith('-'):
                    args[arg_no] += '=' + self.format(option.dest, option.const)
                    self._log(logging.DEBUG, "changed %s for %s", arg, args[arg_no])

        opt, unknown_args = self.parser.parse_args(args or [])
        if unknown_args:
            self.parser.error(f"unrecognized parameters: {' '.join(unknown_args)}")

        if not opt.save and opt.config and not os.access(opt.config, os.R_OK):
            self.parser.error(f"the config file {opt.config!r} selected with -c/--config doesn't exist or is not readable, use -s/--save if you want to generate it")

        # Even if they are not exposed on the CLI, cli un-loadable variables still show up in the opt, remove them
        for option_name in list(vars(opt).keys()):
            if not self.options_index[option_name].cli_loadable:
                delattr(opt, option_name)  # hence list(...) above

        self._load_env_options()
        self._load_cli_options(opt)
        self._load_file_options(self['config'])
        self._postprocess_options()

        if opt.save:
            self.save()

        return opt