def _is_tty_requested(self):

        # check if we require tty (only from our args, cannot see options in configuration files)
        opts = []
        for opt in ('ssh_args', 'ssh_common_args', 'ssh_extra_args'):
            attr = self.get_option(opt)
            if attr is not None:
                opts.extend(self._split_ssh_args(attr))

        args, dummy = self._tty_parser.parse_known_args(opts)

        if args.t:
            return True

        for arg in args.o or []:
            if '=' in arg:
                val = arg.split('=', 1)
            else:
                val = arg.split(maxsplit=1)

            if val[0].lower().strip() == 'requesttty':
                if val[1].lower().strip() in ('yes', 'force'):
                    return True

        return False