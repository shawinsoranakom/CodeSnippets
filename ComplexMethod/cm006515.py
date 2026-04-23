def validate_args(cls, v: list[str] | None) -> list[str] | None:
        """Validate MCP command arguments to prevent shell injection and code execution.

        Blocks shell metacharacters and dangerous flags that could be used for
        command injection, code execution, or package installation attacks.

        Note: -c and /c flags are validated in the model validator where we have
        command context (they're allowed for shell wrappers but not other commands).

        Args:
            v: The list of arguments to validate

        Returns:
            The validated arguments list

        Raises:
            ValueError: If any argument contains dangerous patterns
        """
        if v is None:
            return None

        for arg in v:
            for char in DANGEROUS_SHELL_CHARS:
                if char in arg:
                    msg = f"Argument contains dangerous shell metacharacter '{char}': {arg}"
                    logger.warning("MCP argument rejected - shell metacharacter '{}' in arg", char)
                    raise ValueError(msg)

        # Check dangerous keywords, but skip shell exec flags (validated in model validator)
        for arg in v:
            arg_lower = arg.lower()
            if arg_lower in DANGEROUS_KEYWORDS and arg_lower not in SHELL_EXEC_FLAGS:
                msg = f"Argument '{arg}' is not allowed for security reasons"
                logger.warning("MCP argument rejected - dangerous keyword: '{}'", arg)
                raise ValueError(msg)

        return v