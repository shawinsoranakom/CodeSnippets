def parse_args(self, args=None, namespace=None):
        # Catch missing argument for a better error message
        if self.missing_args_message and not (
            args or any(not arg.startswith("-") for arg in args)
        ):
            self.error(self.missing_args_message)
        return super().parse_args(args, namespace)