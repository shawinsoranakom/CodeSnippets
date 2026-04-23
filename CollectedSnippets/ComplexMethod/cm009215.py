def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: dict,
    ) -> dict:
        """Get the request payload for the Anthropic API."""
        messages = self._convert_input(input_).to_messages()

        for idx, message in enumerate(messages):
            # Translate v1 content
            if (
                isinstance(message, AIMessage)
                and message.response_metadata.get("output_version") == "v1"
            ):
                tcs: list[types.ToolCall] = [
                    {
                        "type": "tool_call",
                        "name": tool_call["name"],
                        "args": tool_call["args"],
                        "id": tool_call.get("id"),
                    }
                    for tool_call in message.tool_calls
                ]
                messages[idx] = message.model_copy(
                    update={
                        "content": _convert_from_v1_to_anthropic(
                            cast(list[types.ContentBlock], message.content),
                            tcs,
                            message.response_metadata.get("model_provider"),
                        )
                    }
                )

        system, formatted_messages = _format_messages(messages)

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "stop_sequences": stop or self.stop_sequences,
            "betas": self.betas,
            "context_management": self.context_management,
            "mcp_servers": self.mcp_servers,
            "system": system,
            **self.model_kwargs,
            **kwargs,
        }
        if self.thinking is not None:
            payload["thinking"] = self.thinking
        if self.inference_geo is not None:
            payload["inference_geo"] = self.inference_geo

        # Handle output_config and effort parameter
        # Priority: self.effort > kwargs output_config > self.output_config
        output_config: dict[str, Any] = {}
        if self.output_config:
            output_config.update(self.output_config)
        payload_oc = payload.get("output_config")
        if isinstance(payload_oc, dict):
            output_config.update(payload_oc)

        if self.effort:
            output_config["effort"] = self.effort

        if output_config:
            payload["output_config"] = output_config

        if "response_format" in payload:
            # response_format present when using agents.create_agent's ProviderStrategy
            # ---
            # ProviderStrategy converts to OpenAI-style format, which passes kwargs to
            # ChatAnthropic, ending up in our payload
            response_format = payload.pop("response_format")
            if (
                isinstance(response_format, dict)
                and response_format.get("type") == "json_schema"
                and "schema" in response_format.get("json_schema", {})
            ):
                response_format = cast(dict, response_format["json_schema"]["schema"])
            # Convert OpenAI-style response_format to Anthropic's output_config.format
            output_config = payload.setdefault("output_config", {})
            output_config["format"] = _convert_to_anthropic_output_config_format(
                response_format
            )

        # Handle deprecated output_format parameter for backward compatibility
        if "output_format" in payload:
            warnings.warn(
                "The 'output_format' parameter is deprecated and will be removed in a "
                "future version. Use 'output_config={\"format\": ...}' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            output_config = payload.setdefault("output_config", {})
            output_config["format"] = payload.pop("output_format")

        if self.reuse_last_container:
            # Check for most recent AIMessage with container set in response_metadata
            # and set as a top-level param on the request
            for message in reversed(messages):
                if (
                    isinstance(message, AIMessage)
                    and (container := message.response_metadata.get("container"))
                    and isinstance(container, dict)
                    and (container_id := container.get("id"))
                ):
                    payload["container"] = container_id
                    break

        # Note: Beta headers are no longer required for structured outputs
        # (output_config.format or strict tool use) as they are now generally available
        if "tools" in payload and isinstance(payload["tools"], list):
            # Auto-append required betas for specific tool types and input_examples
            has_input_examples = False
            for tool in payload["tools"]:
                if isinstance(tool, dict):
                    tool_type = tool.get("type")
                    if tool_type and tool_type in _TOOL_TYPE_TO_BETA:
                        required_beta = _TOOL_TYPE_TO_BETA[tool_type]
                        if payload["betas"]:
                            if required_beta not in payload["betas"]:
                                payload["betas"] = [
                                    *payload["betas"],
                                    required_beta,
                                ]
                        else:
                            payload["betas"] = [required_beta]
                    # Check for input_examples
                    if tool.get("input_examples"):
                        has_input_examples = True

            # Auto-append header for input_examples
            if has_input_examples:
                required_beta = "advanced-tool-use-2025-11-20"
                if payload["betas"]:
                    if required_beta not in payload["betas"]:
                        payload["betas"] = [*payload["betas"], required_beta]
                else:
                    payload["betas"] = [required_beta]

        # Auto-append required beta for mcp_servers
        if payload.get("mcp_servers"):
            required_beta = "mcp-client-2025-11-20"
            if payload["betas"]:
                # Append to existing betas if not already present
                if required_beta not in payload["betas"]:
                    payload["betas"] = [*payload["betas"], required_beta]
            else:
                payload["betas"] = [required_beta]

        # Auto-append required beta for task_budget
        resolved_oc = payload.get("output_config")
        if isinstance(resolved_oc, dict) and resolved_oc.get("task_budget"):
            required_beta = "task-budgets-2026-03-13"
            if payload.get("betas"):
                if required_beta not in payload["betas"]:
                    payload["betas"] = [*payload["betas"], required_beta]
            else:
                payload["betas"] = [required_beta]

        return {k: v for k, v in payload.items() if v is not None}