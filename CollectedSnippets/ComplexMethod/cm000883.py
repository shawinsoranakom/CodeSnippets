async def pre_tool_use_hook(
            input_data: HookInput,
            tool_use_id: str | None,
            context: HookContext,
        ) -> SyncHookJSONOutput:
            """Combined pre-tool-use validation hook."""
            _ = context  # unused but required by signature
            tool_name = cast(str, input_data.get("tool_name", ""))
            tool_input = cast(dict[str, Any], input_data.get("tool_input", {}))

            # Rate-limit sub-agent spawns per session.
            # The SDK CLI renamed "Task" → "Agent" in v2.x; handle both.
            if tool_name in _SUBAGENT_TOOLS:
                # Background agents are allowed — the SDK returns immediately
                # with {isAsync: true} and the model polls via TaskOutput.
                # Still count them against the concurrency limit.
                if len(subagent_tool_use_ids) >= max_subtasks:
                    logger.warning(
                        f"[SDK] Sub-agent limit reached ({max_subtasks}), "
                        f"user={user_id}"
                    )
                    return cast(
                        SyncHookJSONOutput,
                        _deny(
                            f"Maximum {max_subtasks} concurrent sub-agents. "
                            "Wait for running sub-agents to finish, "
                            "or continue in the main conversation."
                        ),
                    )

            # Strip MCP prefix for consistent validation
            is_copilot_tool = tool_name.startswith(MCP_TOOL_PREFIX)
            clean_name = tool_name.removeprefix(MCP_TOOL_PREFIX)

            # Only block non-CoPilot tools; our MCP-registered tools
            # (including Read for oversized results) are already sandboxed.
            if not is_copilot_tool:
                result = _validate_tool_access(clean_name, tool_input, sdk_cwd)
                if result:
                    return cast(SyncHookJSONOutput, result)

            # Validate user isolation
            result = _validate_user_isolation(clean_name, tool_input, user_id)
            if result:
                return cast(SyncHookJSONOutput, result)

            # Reserve the sub-agent slot only after all validations pass
            if tool_name in _SUBAGENT_TOOLS and tool_use_id is not None:
                subagent_tool_use_ids.add(tool_use_id)

            logger.debug(f"[SDK] Tool start: {tool_name}, user={user_id}")
            return cast(SyncHookJSONOutput, {})