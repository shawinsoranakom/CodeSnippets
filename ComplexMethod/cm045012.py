def _resolve_commands_dir(
        parsed_options: dict[str, Any] | None,
        opts: dict[str, Any],
    ) -> str:
        """Extract ``--commands-dir`` from parsed options or raw_options.

        Returns the directory string or raises ``ValueError``.
        """
        parsed_options = parsed_options or {}

        commands_dir = parsed_options.get("commands_dir")
        if commands_dir:
            return commands_dir

        # Fall back to raw_options (--integration-options="--commands-dir ...")
        raw = opts.get("raw_options")
        if raw:
            import shlex
            tokens = shlex.split(raw)
            for i, token in enumerate(tokens):
                if token == "--commands-dir" and i + 1 < len(tokens):
                    return tokens[i + 1]
                if token.startswith("--commands-dir="):
                    return token.split("=", 1)[1]

        raise ValueError(
            "--commands-dir is required for the generic integration"
        )