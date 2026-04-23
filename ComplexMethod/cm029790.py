def take_action(self, action, dest, opt, value, values, parser):
        if action == "store":
            setattr(values, dest, value)
        elif action == "store_const":
            setattr(values, dest, self.const)
        elif action == "store_true":
            setattr(values, dest, True)
        elif action == "store_false":
            setattr(values, dest, False)
        elif action == "append":
            values.ensure_value(dest, []).append(value)
        elif action == "append_const":
            values.ensure_value(dest, []).append(self.const)
        elif action == "count":
            setattr(values, dest, values.ensure_value(dest, 0) + 1)
        elif action == "callback":
            args = self.callback_args or ()
            kwargs = self.callback_kwargs or {}
            self.callback(self, opt, value, parser, *args, **kwargs)
        elif action == "help":
            parser.print_help()
            parser.exit()
        elif action == "version":
            parser.print_version()
            parser.exit()
        else:
            raise ValueError("unknown action %r" % self.action)

        return 1