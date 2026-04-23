def _add_builtin_tool(self, tool_name: str) -> None:
        """Add a built-in tool by name."""
        # Skip if an identical tool has already been registered (idempotent behaviour)
        if any(td.get("type") == tool_name for td in self._tools):
            return  # Duplicate – ignore rather than raise to stay backward-compatible
        # Only allow string format for tools that don't require parameters
        if tool_name == "web_search_preview":
            self._tools.append({"type": "web_search_preview"})
        elif tool_name == "image_generation":
            self._tools.append({"type": "image_generation"})
        elif tool_name == "local_shell":
            # Special handling for local_shell - very limited model support
            if self._model != "codex-mini-latest":
                raise ValueError(
                    f"Tool 'local_shell' is only supported with model 'codex-mini-latest', "
                    f"but current model is '{self._model}'. "
                    f"This tool is available exclusively through the Responses API and has severe limitations. "
                    f"Consider using autogen_ext.tools.code_execution.PythonCodeExecutionTool with "
                    f"autogen_ext.code_executors.local.LocalCommandLineCodeExecutor for shell execution instead."
                )
            self._tools.append({"type": "local_shell"})
        elif tool_name in ["file_search", "code_interpreter", "computer_use_preview", "mcp"]:
            # These tools require specific parameters and must use dict configuration
            raise ValueError(
                f"Tool '{tool_name}' requires specific parameters and cannot be added using string format. "
                f"Use dict configuration instead. Required parameters for {tool_name}: "
                f"{self._get_required_params_help(tool_name)}"
            )
        else:
            raise ValueError(f"Unsupported built-in tool type: {tool_name}")