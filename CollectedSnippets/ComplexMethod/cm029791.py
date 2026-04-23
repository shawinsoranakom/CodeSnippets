def _check_conflict(self, option):
        conflict_opts = []
        for opt in option._short_opts:
            if opt in self._short_opt:
                conflict_opts.append((opt, self._short_opt[opt]))
        for opt in option._long_opts:
            if opt in self._long_opt:
                conflict_opts.append((opt, self._long_opt[opt]))

        if conflict_opts:
            handler = self.conflict_handler
            if handler == "error":
                raise OptionConflictError(
                    "conflicting option string(s): %s"
                    % ", ".join([co[0] for co in conflict_opts]),
                    option)
            elif handler == "resolve":
                for (opt, c_option) in conflict_opts:
                    if opt.startswith("--"):
                        c_option._long_opts.remove(opt)
                        del self._long_opt[opt]
                    else:
                        c_option._short_opts.remove(opt)
                        del self._short_opt[opt]
                    if not (c_option._short_opts or c_option._long_opts):
                        c_option.container.option_list.remove(c_option)