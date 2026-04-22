def _require_arg(args: Dict[str, List[bytes]], name: str) -> str:
        """Return the value of the argument with the given name.

        A human-readable exception will be raised if the argument doesn't
        exist. This will be used as the body for the error response returned
        from the request.
        """
        try:
            arg = args[name]
        except KeyError:
            raise Exception(f"Missing '{name}'")

        if len(arg) != 1:
            raise Exception(f"Expected 1 '{name}' arg, but got {len(arg)}")

        # Convert bytes to string
        return arg[0].decode("utf-8")