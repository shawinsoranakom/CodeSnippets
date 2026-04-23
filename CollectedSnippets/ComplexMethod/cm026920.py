async def async_add_delta_content_stream(
        self,
        agent_id: str,
        stream: AsyncIterable[AssistantContentDeltaDict | ToolResultContentDeltaDict],
    ) -> AsyncGenerator[AssistantContent | ToolResultContent]:
        """Stream content into the chat log.

        Returns a generator with all content that was added to the chat log.

        stream iterates over dictionaries with optional keys role, content and tool_calls.

        When a delta contains a role key, the current message is considered complete and
        a new message is started.

        The keys content and tool_calls will be concatenated if they appear multiple times.
        """
        current_content = ""
        current_thinking_content = ""
        current_native: Any = None
        current_tool_calls: list[llm.ToolInput] = []
        tool_call_tasks: dict[str, asyncio.Task] = {}

        async for delta in stream:
            LOGGER.debug("Received delta: %s", delta)

            # Indicates update to current message
            if "role" not in delta:
                # ToolResultContentDeltaDict will always have a role
                assistant_delta = cast(AssistantContentDeltaDict, delta)
                if delta_content := assistant_delta.get("content"):
                    current_content += delta_content
                if delta_thinking_content := assistant_delta.get("thinking_content"):
                    current_thinking_content += delta_thinking_content
                if delta_native := assistant_delta.get("native"):
                    if current_native is not None:
                        raise RuntimeError(
                            "Native content already set, cannot overwrite"
                        )
                    current_native = delta_native
                if delta_tool_calls := assistant_delta.get("tool_calls"):
                    current_tool_calls += delta_tool_calls

                    # Start processing the tool calls as soon as we know about them
                    for tool_call in delta_tool_calls:
                        if not tool_call.external:
                            if self.llm_api is None:
                                raise ValueError("No LLM API configured")

                            tool_call_tasks[tool_call.id] = self.hass.async_create_task(
                                self.llm_api.async_call_tool(tool_call),
                                name=f"llm_tool_{tool_call.id}",
                            )
                if self.delta_listener:
                    if filtered_delta := {
                        k: v for k, v in assistant_delta.items() if k != "native"
                    }:
                        # We do not want to send the native content to the listener
                        # as it is not JSON serializable
                        self.delta_listener(self, filtered_delta)
                continue

            # Starting a new message
            # Yield the previous message if it has content
            if (
                current_content
                or current_thinking_content
                or current_tool_calls
                or current_native
            ):
                content: AssistantContent | ToolResultContent = AssistantContent(
                    agent_id=agent_id,
                    content=current_content or None,
                    thinking_content=current_thinking_content or None,
                    tool_calls=current_tool_calls or None,
                    native=current_native,
                )
                yield content
                async for tool_result in self.async_add_assistant_content(
                    content, tool_call_tasks=tool_call_tasks
                ):
                    yield tool_result
                    if self.delta_listener:
                        self.delta_listener(self, asdict(tool_result))
                current_content = ""
                current_thinking_content = ""
                current_native = None
                current_tool_calls = []

            if delta["role"] == "assistant":
                current_content = delta.get("content") or ""
                current_thinking_content = delta.get("thinking_content") or ""
                current_tool_calls = delta.get("tool_calls") or []
                current_native = delta.get("native")

                if self.delta_listener:
                    if filtered_delta := {
                        k: v for k, v in delta.items() if k != "native"
                    }:
                        self.delta_listener(self, filtered_delta)
            elif delta["role"] == "tool_result":
                content = ToolResultContent(
                    agent_id=agent_id,
                    tool_call_id=delta["tool_call_id"],
                    tool_name=delta["tool_name"],
                    tool_result=delta["tool_result"],
                )
                yield content
                if self.delta_listener:
                    self.delta_listener(self, asdict(content))
                self.async_add_assistant_content_without_tools(content)
            else:
                raise ValueError(
                    "Only assistant and tool_result roles expected."
                    f" Got {delta['role']}"
                )

        if (
            current_content
            or current_thinking_content
            or current_tool_calls
            or current_native
        ):
            content = AssistantContent(
                agent_id=agent_id,
                content=current_content or None,
                thinking_content=current_thinking_content or None,
                tool_calls=current_tool_calls or None,
                native=current_native,
            )
            yield content
            async for tool_result in self.async_add_assistant_content(
                content, tool_call_tasks=tool_call_tasks
            ):
                yield tool_result
                if self.delta_listener:
                    self.delta_listener(self, asdict(tool_result))