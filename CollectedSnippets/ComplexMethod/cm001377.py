def _generalize_pattern(self, command_name: str, args_str: str) -> str:
        """Create a generalized pattern from specific command args.

        Args:
            command_name: Name of the command.
            args_str: Formatted arguments string.

        Returns:
            Generalized permission pattern.
        """
        # For file paths, generalize to parent directory
        if command_name in ("read_file", "write_to_file", "list_folder"):
            path = Path(args_str)
            # If within workspace, use {workspace} placeholder
            try:
                rel = path.resolve().relative_to(self.workspace)
                return f"{command_name}({{workspace}}/{rel.parent}/*)"
            except ValueError:
                # Outside workspace, use exact path
                return f"{command_name}({path})"

        # For shell commands, use executable:** pattern
        if command_name in ("execute_shell", "execute_python"):
            # args_str is in format "executable:args", extract executable
            if ":" in args_str:
                executable = args_str.split(":", 1)[0]
                return f"{command_name}({executable}:**)"
            return f"{command_name}(*)"

        # For web operations
        if command_name == "web_search":
            return "web_search(**)"
        if command_name == "read_webpage":
            # Extract domain
            match = re.match(r"https?://([^/]+)", args_str)
            if match:
                domain = match.group(1)
                return f"read_webpage(*{domain}*)"
            return "read_webpage(**)"

        # Generic: use ** wildcard to match any arguments including those with /
        return f"{command_name}(**)"