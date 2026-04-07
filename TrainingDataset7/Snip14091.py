def resolve(self, path):
        match = self.pattern.match(path)
        if match:
            new_path, args, captured_kwargs = match
            # Pass any default args as **kwargs.
            kwargs = {**captured_kwargs, **self.default_args}
            return ResolverMatch(
                self.callback,
                args,
                kwargs,
                self.pattern.name,
                route=str(self.pattern),
                captured_kwargs=captured_kwargs,
                extra_kwargs=self.default_args,
            )