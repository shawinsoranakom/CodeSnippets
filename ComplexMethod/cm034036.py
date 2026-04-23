def _clean_args(self, args):

        if not self._clean:
            # create a printable version of the command for use in reporting later,
            # which strips out things like passwords from the args list
            to_clean_args = args
            if isinstance(args, bytes):
                to_clean_args = to_text(args)
            if isinstance(args, (str, bytes)):
                to_clean_args = shlex.split(to_clean_args)

            clean_args = []
            is_passwd = False
            for arg in (to_native(a) for a in to_clean_args):
                if is_passwd:
                    is_passwd = False
                    clean_args.append('********')
                    continue
                if PASSWD_ARG_RE.match(arg):
                    sep_idx = arg.find('=')
                    if sep_idx > -1:
                        clean_args.append('%s=********' % arg[:sep_idx])
                        continue
                    else:
                        is_passwd = True
                arg = heuristic_log_sanitize(arg, self.no_log_values)
                clean_args.append(arg)
            self._clean = ' '.join(shlex.quote(arg) for arg in clean_args)

        return self._clean