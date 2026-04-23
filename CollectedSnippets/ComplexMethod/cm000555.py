async def _execute_tools_sdk_mode(
        self,
        input_data: "OrchestratorBlock.Input",
        credentials: llm.APIKeyCredentials,
        tool_functions: list[dict[str, Any]],
        prompt: list[dict[str, Any]],
        execution_params: ExecutionParams,
        execution_processor: "ExecutionProcessor",
    ):
        """Execute tools using the Claude Agent SDK.

        The SDK manages the conversation loop and tool calling natively.
        Graph-connected blocks are exposed as MCP tools.
        """
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ClaudeSDKClient,
            ResultMessage,
            TextBlock,
            ToolResultBlock,
            ToolUseBlock,
            UserMessage,
        )

        # Build MCP server from graph-connected tools
        mcp_server = self._create_graph_mcp_server(
            tool_functions, execution_params, execution_processor
        )

        # Build allowed tools list (MCP-prefixed names).
        # Derive the prefix from the class-level server name constant.
        MCP_PREFIX = f"mcp__{self._SDK_MCP_SERVER_NAME}__"
        allowed_tools = [
            f"{MCP_PREFIX}{tf['function']['name']}" for tf in tool_functions
        ]

        # Disable ALL known SDK built-in tools — only graph MCP tools available.
        # `allowed_tools` (above) is the primary restriction: the SDK only
        # enables tools explicitly listed there.  This blocklist is a
        # defense-in-depth measure in case the SDK's allowlist logic changes.
        # IMPORTANT: Keep this list in sync with the Claude Agent SDK.
        # If a new built-in tool is added in a future SDK version, it will
        # still be blocked by `allowed_tools` (only MCP-prefixed names are
        # allowed), but adding it here provides an extra safety layer.
        disallowed_tools = [
            "Bash",
            "WebFetch",
            "AskUserQuestion",
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "Task",
            "WebSearch",
            "TodoWrite",
            "NotebookEdit",
        ]

        # Build SDK env — provider-aware credential routing.
        # Extended thinking does not support subscription-mode (platform-managed credits).
        # Use *credential* provider for routing (not model metadata provider),
        # because a user may select an Anthropic model but route through OpenRouter.
        provider = credentials.provider
        if not credentials.api_key:
            yield (
                "error",
                (
                    "Extended thinking requires direct API credentials and does not "
                    "support subscription mode. Please provide an Anthropic or OpenRouter API key."
                ),
            )
            return
        api_key = credentials.api_key.get_secret_value()
        if provider == "open_router":
            # Route through OpenRouter proxy: set base URL + auth token,
            # clear API key so the SDK uses AUTH_TOKEN instead.
            # NOTE: We use the platform's global OpenRouter base URL from
            # ChatConfig.  Per-credential base URLs are not yet supported;
            # if the user's credential targets a custom proxy, the SDK will
            # still route through the platform's configured endpoint.
            or_base = (copilot_config.base_url or "https://openrouter.ai/api").rstrip(
                "/"
            )
            if or_base.endswith("/v1"):
                or_base = or_base[:-3]
            sdk_env = {
                "ANTHROPIC_BASE_URL": or_base,
                "ANTHROPIC_AUTH_TOKEN": api_key,
                "ANTHROPIC_API_KEY": "",  # force CLI to use AUTH_TOKEN
            }
        else:
            # Direct Anthropic key
            sdk_env = {"ANTHROPIC_API_KEY": api_key}

        # Use an execution-specific working directory to prevent concurrent
        # SDK executions from colliding.  tempfile.mkdtemp() respects TMPDIR
        # and works in containerised environments with read-only root filesystems.
        sdk_cwd = tempfile.mkdtemp(
            prefix=f"orchestrator-sdk-{execution_params.graph_exec_id}-"
        )

        response_parts: list[str] = []
        conversation: list[dict[str, Any]] = list(prompt)  # Start with input prompt
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_usd: float | None = None

        sdk_error: Exception | None = None
        try:
            # Build SDK options
            options = ClaudeAgentOptions(
                system_prompt=input_data.sys_prompt or "",
                mcp_servers={self._SDK_MCP_SERVER_NAME: mcp_server},
                allowed_tools=allowed_tools,
                disallowed_tools=disallowed_tools,
                cwd=sdk_cwd,
                env=sdk_env,
                model=input_data.model.value or None,
            )

            # Strip system messages from prompt — they're already passed via
            # ClaudeAgentOptions.system_prompt to avoid sending them twice.
            sdk_prompt = [p for p in prompt if p.get("role") != "system"]

            # Build user message from prompt.
            # The SDK's query() accepts a string or an async iterable of message dicts.
            # For multi-turn conversations, pass the full history as an async iterable
            # to preserve assistant replies, tool calls/results, and system messages.
            has_multi_turn = any(
                p.get("role") in ("assistant", "tool") for p in sdk_prompt
            )
            if has_multi_turn:

                async def _prompt_iter():
                    for p in sdk_prompt:
                        yield p

                user_message: str | AsyncIterable[dict[str, Any]] = _prompt_iter()
            else:
                # Single-turn: collapse user content into one string
                user_parts = []
                for p in sdk_prompt:
                    if p.get("role") == "user" and p.get("content"):
                        user_parts.append(str(p["content"]))
                user_message = (
                    "\n\n".join(user_parts) if user_parts else input_data.prompt
                )

            # Run SDK client with heartbeat-safe message iteration.
            # We must NOT cancel __anext__() mid-flight — doing so corrupts
            # the SDK's internal anyio memory stream (same pattern as
            # copilot/sdk/service.py:_iter_sdk_messages).

            _HEARTBEAT_INTERVAL = 10.0  # seconds
            async with ClaudeSDKClient(options=options) as client:
                await client.query(user_message)

                msg_iter = client.receive_response().__aiter__()
                pending_task: asyncio.Task[Any] | None = None

                async def _next_msg() -> Any:
                    return await msg_iter.__anext__()

                try:
                    while True:
                        if pending_task is None:
                            pending_task = asyncio.create_task(_next_msg())

                        done, _ = await asyncio.wait(
                            {pending_task}, timeout=_HEARTBEAT_INTERVAL
                        )

                        if not done:
                            # Heartbeat — SDK is still processing, keep waiting
                            continue

                        pending_task = None
                        try:
                            sdk_msg = done.pop().result()
                        except StopAsyncIteration:
                            break

                        if isinstance(sdk_msg, AssistantMessage):
                            text_parts = []
                            tool_use_parts = []
                            for content_block in sdk_msg.content:
                                if isinstance(content_block, TextBlock):
                                    text_parts.append(content_block.text)
                                    response_parts.append(content_block.text)
                                elif isinstance(content_block, ToolUseBlock):
                                    raw_name = getattr(content_block, "name", "unknown")
                                    # Strip MCP prefix for readability in
                                    # conversation history.
                                    clean_name = raw_name.removeprefix(MCP_PREFIX)
                                    tool_use_parts.append(
                                        {
                                            "tool": clean_name,
                                            "id": getattr(
                                                content_block, "id", "unknown"
                                            ),
                                        }
                                    )
                            if text_parts or tool_use_parts:
                                msg_content = "".join(text_parts)
                                if tool_use_parts:
                                    tool_summary = ", ".join(
                                        t["tool"] for t in tool_use_parts
                                    )
                                    if msg_content:
                                        msg_content += f"\n[Tool calls: {tool_summary}]"
                                    else:
                                        msg_content = f"[Tool calls: {tool_summary}]"
                                conversation.append(
                                    {
                                        "role": "assistant",
                                        "content": msg_content,
                                    }
                                )
                        elif isinstance(sdk_msg, UserMessage):
                            # Capture tool results so the conversation
                            # history records what each tool returned.
                            result_parts: list[str] = []
                            for block in getattr(sdk_msg, "content", []):
                                if isinstance(block, ToolResultBlock):
                                    content_val = getattr(block, "content", "")
                                    if isinstance(content_val, list):
                                        # list of text blocks
                                        for item in content_val:
                                            if isinstance(item, dict):
                                                result_parts.append(
                                                    item.get("text", "")
                                                )
                                    elif content_val:
                                        result_parts.append(str(content_val))
                            if result_parts:
                                conversation.append(
                                    {
                                        "role": "tool",
                                        "content": "\n".join(result_parts),
                                    }
                                )
                        elif isinstance(sdk_msg, ResultMessage):
                            if sdk_msg.usage:
                                total_prompt_tokens += getattr(
                                    sdk_msg.usage, "input_tokens", 0
                                )
                                total_completion_tokens += getattr(
                                    sdk_msg.usage, "output_tokens", 0
                                )
                            if sdk_msg.total_cost_usd is not None:
                                total_cost_usd = sdk_msg.total_cost_usd
                finally:
                    if pending_task is not None and not pending_task.done():
                        pending_task.cancel()
                        try:
                            await pending_task
                        except (asyncio.CancelledError, StopAsyncIteration):
                            pass
        except InsufficientBalanceError:
            # IBE must propagate — see class docstring. The `finally`
            # block below still runs and records partial token usage.
            raise
        except Exception as e:
            # Surface OTHER SDK errors as user-visible output instead
            # of crashing, consistent with _execute_tools_agent_mode
            # error handling. Don't return yet — fall through to
            # merge_stats below so partial token usage is always recorded.
            sdk_error = e
        finally:
            # Always record usage stats, even on error.  The SDK may have
            # made LLM calls (consuming tokens) before the failure; dropping
            # those stats would under-count resource usage.
            # llm_call_count=1 is approximate; the SDK manages its own
            # multi-turn loop and only exposes aggregate usage.
            if (
                total_prompt_tokens > 0
                or total_completion_tokens > 0
                or total_cost_usd is not None
            ):
                self.merge_stats(
                    NodeExecutionStats(
                        input_token_count=total_prompt_tokens,
                        output_token_count=total_completion_tokens,
                        llm_call_count=1,
                        provider_cost=total_cost_usd,
                    )
                )
            # Clean up execution-specific working directory.
            shutil.rmtree(sdk_cwd, ignore_errors=True)

        if sdk_error is not None:
            yield "error", str(sdk_error)
            return

        response_text = "".join(response_parts)

        yield "finished", response_text
        yield "conversations", conversation