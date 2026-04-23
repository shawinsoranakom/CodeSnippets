def _showwarning(
        self, message, category, filename, lineno, *args, use_warnmsg=None, **kwargs
    ):
        for cat, _, pattern, mod, rec in (self._suppressions + self._tmp_suppressions)[
            ::-1
        ]:
            if issubclass(category, cat) and pattern.match(message.args[0]) is not None:
                if mod is None:
                    # Message and category match, either recorded or ignored
                    if rec is not None:
                        msg = WarningMessage(
                            message, category, filename, lineno, **kwargs
                        )
                        self.log.append(msg)
                        rec.append(msg)
                    return
                # Use startswith, because warnings strips the c or o from
                # .pyc/.pyo files.
                elif mod.__file__.startswith(filename):
                    # The message and module (filename) match
                    if rec is not None:
                        msg = WarningMessage(
                            message, category, filename, lineno, **kwargs
                        )
                        self.log.append(msg)
                        rec.append(msg)
                    return

        # There is no filter in place, so pass to the outside handler
        # unless we should only pass it once
        if self._forwarding_rule == "always":
            if use_warnmsg is None:
                self._orig_show(message, category, filename, lineno, *args, **kwargs)
            else:
                self._orig_showmsg(use_warnmsg)
            return

        if self._forwarding_rule == "once":
            signature = (message.args, category)
        elif self._forwarding_rule == "module":
            signature = (message.args, category, filename)
        elif self._forwarding_rule == "location":
            signature = (message.args, category, filename, lineno)

        if signature in self._forwarded:
            return
        self._forwarded.add(signature)
        if use_warnmsg is None:
            self._orig_show(message, category, filename, lineno, *args, **kwargs)
        else:
            self._orig_showmsg(use_warnmsg)